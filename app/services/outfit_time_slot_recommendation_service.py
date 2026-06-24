from typing import Literal

from app.schemas.outfit_response import OutfitSelection
from app.schemas.outfit_time_slot_request import (
    TimeSlotOutfitRecommendationRequest,
)
from app.schemas.outfit_time_slot_response import (
    TimeSlotOutfitBatchRecommendationResponse,
    TimeSlotOutfitRecommendation,
)
from app.services.gemini_outfit_service import (
    GeminiOutfitGenerationError,
    GeminiOutfitService,
)
from app.services.outfit_catalog import (
    InvalidOutfitSelectionError,
    OutfitCatalog,
)
from app.services.outfit_recommendation_cache import OutfitRecommendationCache
from app.services.outfit_time_slot_rule_engine import TimeSlotOutfitRuleEngine



class TimeSlotOutfitRecommendationService:
    def __init__(
        self,
        rule_engine: TimeSlotOutfitRuleEngine | None = None,
        catalog: OutfitCatalog | None = None,
        gemini_outfit_service: GeminiOutfitService | None = None,
        cache: OutfitRecommendationCache | None = None,
    ) -> None:
        self.rule_engine = rule_engine or TimeSlotOutfitRuleEngine()
        self.catalog = catalog or OutfitCatalog()
        self.gemini_outfit_service = (
            gemini_outfit_service or GeminiOutfitService(self.catalog)
        )
        self.cache = cache or OutfitRecommendationCache()

    def recommend(
        self,
        request: TimeSlotOutfitRecommendationRequest,
    ) -> TimeSlotOutfitBatchRecommendationResponse:
        cache_key = self.cache.create_key(request)
        cached_result = self.cache.get(cache_key)

        if cached_result is not None:
            return self._build_response(
                request=request,
                selections=cached_result.selections,
                source=cached_result.source,
            )

        fallback_selections = self._create_fallback_selections(request)

        self.cache.save(
            cache_key,
            source="fallback",
            selections=fallback_selections,
        )

        return self._build_response(
            request=request,
            selections=fallback_selections,
            source="fallback",
        )

    def reserve_warmup(
        self,
        request: TimeSlotOutfitRecommendationRequest,
    ) -> bool:
        return self.cache.reserve_warmup(
            self.cache.create_key(request)
        )

    def warm_cache(
        self,
        request: TimeSlotOutfitRecommendationRequest,
    ) -> None:
        cache_key = self.cache.create_key(request)
        succeeded = False

        try:
            cached_result = self.cache.get(cache_key)

            if cached_result is not None and cached_result.source == "ai":
                succeeded = True
                return

            fallback_selections = (
                cached_result.selections
                if cached_result is not None
                else self._create_fallback_selections(request)
            )

            gemini_result = self.gemini_outfit_service.generate_time_slots(
                request=request,
                fallback_selections=fallback_selections,
            )

            selections = gemini_result.to_time_slot_selections()

            self._validate_time_slot_selections(
                request=request,
                selections=selections,
            )

            self.cache.save(
                cache_key,
                source="ai",
                selections=selections,
            )

            succeeded = True

        except (
            GeminiOutfitGenerationError,
            InvalidOutfitSelectionError,
        ):
            pass

        except Exception:
            pass

        finally:
            self.cache.complete_warmup(
                cache_key,
                succeeded=succeeded,
            )

    def _create_fallback_selections(
        self,
        request: TimeSlotOutfitRecommendationRequest,
    ) -> dict[str, OutfitSelection]:
        return {
            time_slot_weather.timeSlot: self.rule_engine.select(
                region=request.region,
                time_slot_weather=time_slot_weather,
            )
            for time_slot_weather in request.timeSlots
        }

    def _validate_time_slot_selections(
        self,
        *,
        request: TimeSlotOutfitRecommendationRequest,
        selections: dict[str, OutfitSelection],
    ) -> None:
        requested_time_slots = {
            time_slot_weather.timeSlot
            for time_slot_weather in request.timeSlots
        }

        if set(selections.keys()) != requested_time_slots:
            raise InvalidOutfitSelectionError(
                "Gemini 시간대별 추천 응답 구성이 올바르지 않습니다."
            )

        for time_slot_weather in request.timeSlots:
            self.catalog.validate_selection(
                selections[time_slot_weather.timeSlot]
            )

    def _build_response(
        self,
        *,
        request: TimeSlotOutfitRecommendationRequest,
        selections: dict[str, OutfitSelection],
        source: Literal["ai", "fallback"],
    ) -> TimeSlotOutfitBatchRecommendationResponse:
        recommendations: list[TimeSlotOutfitRecommendation] = []

        for time_slot_weather in request.timeSlots:
            outfit_response = self.catalog.build_response(
                region=request.region,
                travel_style=time_slot_weather.timeSlotName,
                selection=selections[time_slot_weather.timeSlot],
                source=source,
            )

            recommendations.append(
                TimeSlotOutfitRecommendation(
                    timeSlot=time_slot_weather.timeSlot,
                    timeSlotName=time_slot_weather.timeSlotName,
                    forecastAt=time_slot_weather.forecastAt,
                    startTime=time_slot_weather.startTime,
                    endTime=time_slot_weather.endTime,
                    outfitCards=outfit_response.outfitCards,
                    preparationItems=outfit_response.preparationItems,
                )
            )

        return TimeSlotOutfitBatchRecommendationResponse(
            region=request.region,
            source=source,
            recommendations=recommendations,
        )


time_slot_outfit_recommendation_service = (
    TimeSlotOutfitRecommendationService()
)
