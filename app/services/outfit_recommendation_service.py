from typing import Literal

from app.schemas.outfit_batch_request import OutfitBatchRecommendationRequest
from app.schemas.outfit_batch_response import (
    TRAVEL_STYLES, OutfitBatchRecommendationResponse)
from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import (OutfitRecommendationResponse,
                                         OutfitSelection)
from app.services.gemini_outfit_service import (GeminiOutfitGenerationError,
                                                GeminiOutfitService)
from app.services.outfit_catalog import (InvalidOutfitSelectionError,
                                         OutfitCatalog)
from app.services.outfit_recommendation_cache import OutfitRecommendationCache
from app.services.outfit_rule_engine import OutfitRuleEngine


class OutfitRecommendationService:
    def __init__(
        self,
        rule_engine: OutfitRuleEngine | None = None,
        catalog: OutfitCatalog | None = None,
        gemini_outfit_service: GeminiOutfitService | None = None,
        cache: OutfitRecommendationCache | None = None,
    ) -> None:
        self.rule_engine = rule_engine or OutfitRuleEngine()
        self.catalog = catalog or OutfitCatalog()
        self.gemini_outfit_service = (
            gemini_outfit_service or GeminiOutfitService(self.catalog)
        )
        self.cache = cache or OutfitRecommendationCache()

    def recommend(
        self,
        request: OutfitRecommendationRequest,
    ) -> OutfitRecommendationResponse:
        fallback_selection = self.rule_engine.select(request)

        try:
            gemini_selection = self.gemini_outfit_service.generate(
                request=request,
                fallback_selection=fallback_selection,
            )

            return self.catalog.build_response(
                region=request.region,
                travel_style=request.travelStyle,
                selection=gemini_selection,
                source="ai",
            )

        except (
            GeminiOutfitGenerationError,
            InvalidOutfitSelectionError,
        ):
            return self.catalog.build_response(
                region=request.region,
                travel_style=request.travelStyle,
                selection=fallback_selection,
                source="fallback",
            )

    def recommend_batch(
        self,
        request: OutfitBatchRecommendationRequest,
    ) -> OutfitBatchRecommendationResponse:
        cache_key = self.cache.create_key(request)
        cached_result = self.cache.get(cache_key)

        if cached_result is not None:
            return self._build_batch_response(
                region=request.region,
                selections=cached_result.selections,
                source=cached_result.source,
            )

        fallback_selections = self._create_fallback_selections(request)

        self.cache.save(
            cache_key,
            source="fallback",
            selections=fallback_selections,
        )

        return self._build_batch_response(
            region=request.region,
            selections=fallback_selections,
            source="fallback",
        )

    def reserve_batch_warmup(
        self,
        request: OutfitBatchRecommendationRequest,
    ) -> bool:
        cache_key = self.cache.create_key(request)

        return self.cache.reserve_warmup(cache_key)

    def warm_batch_cache(
        self,
        request: OutfitBatchRecommendationRequest,
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

            gemini_batch_selection = (
                self.gemini_outfit_service.generate_batch(
                    request=request,
                    fallback_selections=fallback_selections,
                )
            )

            selections = gemini_batch_selection.to_style_selections()

            self._validate_batch_selections(selections)

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

        finally:
            self.cache.complete_warmup(
                cache_key,
                succeeded=succeeded,
            )

    def _create_fallback_selections(
        self,
        request: OutfitBatchRecommendationRequest,
    ) -> dict[str, OutfitSelection]:
        return {
            travel_style: self.rule_engine.select(
                OutfitRecommendationRequest(
                    region=request.region,
                    travelStyle=travel_style,
                    currentWeather=request.currentWeather,
                    feelsLikeWeather=request.feelsLikeWeather,
                )
            )
            for travel_style in TRAVEL_STYLES
        }

    def _validate_batch_selections(
        self,
        selections: dict[str, OutfitSelection],
    ) -> None:
        if set(selections.keys()) != set(TRAVEL_STYLES):
            raise InvalidOutfitSelectionError(
                "Gemini 배치 응답의 여행 스타일 구성이 올바르지 않습니다."
            )

        for travel_style in TRAVEL_STYLES:
            self.catalog.validate_selection(selections[travel_style])

    def _build_batch_response(
        self,
        *,
        region: str,
        selections: dict[str, OutfitSelection],
        source: Literal["ai", "fallback"],
    ) -> OutfitBatchRecommendationResponse:
        recommendations = {
            travel_style: self.catalog.build_response(
                region=region,
                travel_style=travel_style,
                selection=selections[travel_style],
                source=source,
            )
            for travel_style in TRAVEL_STYLES
        }

        return OutfitBatchRecommendationResponse(
            region=region,
            source=source,
            recommendations=recommendations,
        )


outfit_recommendation_service = OutfitRecommendationService()