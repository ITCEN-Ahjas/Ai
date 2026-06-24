from app.schemas.outfit_response import OutfitSelection
from app.schemas.outfit_time_slot_request import (
    TimeSlotOutfitRecommendationRequest,
)
from app.schemas.outfit_time_slot_response import (
    TimeSlotOutfitSelection,
    TimeSlotOutfitSelectionBatch,
)
from app.services.gemini_outfit_service import GeminiOutfitGenerationError
from app.services.outfit_recommendation_cache import OutfitRecommendationCache
from app.services.outfit_time_slot_recommendation_service import (
    TimeSlotOutfitRecommendationService,
)
from app.services.outfit_time_slot_rule_engine import TimeSlotOutfitRuleEngine


class FakeGeminiTimeSlotSuccessService:
    def __init__(self) -> None:
        self.call_count = 0

    def generate_time_slots(
        self,
        request: TimeSlotOutfitRecommendationRequest,
        fallback_selections: dict[str, OutfitSelection],
    ) -> TimeSlotOutfitSelectionBatch:
        self.call_count += 1

        return TimeSlotOutfitSelectionBatch(
            recommendations=[
                TimeSlotOutfitSelection(
                    timeSlot="afternoon",
                    outerwearCode="windbreaker",
                    topCode="long_sleeve_tshirt",
                    bottomCode="cotton_pants",
                    shoesCode="sneakers",
                    preparationCodes=["light_outerwear", "water_bottle"],
                ),
                TimeSlotOutfitSelection(
                    timeSlot="evening",
                    outerwearCode="light_jacket",
                    topCode="long_sleeve_tshirt",
                    bottomCode="jeans",
                    shoesCode="sneakers",
                    preparationCodes=["light_outerwear", "battery"],
                ),
            ]
        )


class FakeGeminiTimeSlotFailureService:
    def __init__(self) -> None:
        self.call_count = 0

    def generate_time_slots(
        self,
        request: TimeSlotOutfitRecommendationRequest,
        fallback_selections: dict[str, OutfitSelection],
    ) -> TimeSlotOutfitSelectionBatch:
        self.call_count += 1
        raise GeminiOutfitGenerationError("Gemini 호출 실패")


def create_request() -> TimeSlotOutfitRecommendationRequest:
    return TimeSlotOutfitRecommendationRequest(
        region="청주",
        timeSlots=[
            {
                "timeSlot": "afternoon",
                "timeSlotName": "오후",
                "forecastAt": "2026-06-24T15:00:00",
                "startTime": "14:00",
                "endTime": "17:00",
                "currentWeather": {
                    "temperature": 26.0,
                    "humidity": 55,
                    "windSpeed": 4.1,
                    "windStatus": "보통",
                    "precipitationAmount": "강수 없음",
                    "precipitationType": "강수 없음",
                    "precipitationProbability": 30,
                    "skyStatus": "흐림",
                    "weatherCondition": "흐림",
                },
                "feelsLikeWeather": {
                    "feelsLikeTemperature": 26.0,
                    "temperatureDifference": 0.0,
                    "description": "현재 기온과 비슷하게 느껴집니다.",
                    "factors": ["현재 기온"],
                },
            },
            {
                "timeSlot": "evening",
                "timeSlotName": "저녁",
                "forecastAt": "2026-06-24T19:00:00",
                "startTime": "17:00",
                "endTime": "21:00",
                "currentWeather": {
                    "temperature": 23.0,
                    "humidity": 70,
                    "windSpeed": 3.0,
                    "windStatus": "보통",
                    "precipitationAmount": "강수 없음",
                    "precipitationType": "강수 없음",
                    "precipitationProbability": 20,
                    "skyStatus": "구름 많음",
                    "weatherCondition": "구름 많음",
                },
                "feelsLikeWeather": {
                    "feelsLikeTemperature": 23.0,
                    "temperatureDifference": 0.0,
                    "description": "현재 기온과 비슷하게 느껴집니다.",
                    "factors": ["현재 기온"],
                },
            },
        ],
    )


def create_service(gemini_outfit_service) -> TimeSlotOutfitRecommendationService:
    return TimeSlotOutfitRecommendationService(
        rule_engine=TimeSlotOutfitRuleEngine(),
        gemini_outfit_service=gemini_outfit_service,
        cache=OutfitRecommendationCache(
            ttl_seconds=600,
            failure_retry_seconds=300,
        ),
    )


def test_returns_fallback_immediately_for_remaining_time_slots() -> None:
    service = create_service(FakeGeminiTimeSlotSuccessService())

    response = service.recommend(create_request())

    assert response.source == "fallback"
    assert [item.timeSlot for item in response.recommendations] == [
        "afternoon",
        "evening",
    ]
    assert response.recommendations[0].outfitCards.top.code
    assert response.recommendations[1].outfitCards.outerwear.code == (
        "light_jacket"
    )


def test_returns_cached_ai_result_after_warmup() -> None:
    gemini_service = FakeGeminiTimeSlotSuccessService()
    service = create_service(gemini_service)
    request = create_request()

    first_response = service.recommend(request)

    assert first_response.source == "fallback"
    assert gemini_service.call_count == 0
    assert service.reserve_warmup(request) is True

    service.warm_cache(request)

    second_response = service.recommend(request)

    assert second_response.source == "ai"
    assert gemini_service.call_count == 1
    assert second_response.recommendations[0].outfitCards.outerwear.code == (
        "windbreaker"
    )
    assert second_response.recommendations[1].outfitCards.outerwear.code == (
        "light_jacket"
    )


def test_keeps_fallback_cache_when_gemini_generation_fails() -> None:
    gemini_service = FakeGeminiTimeSlotFailureService()
    service = create_service(gemini_service)
    request = create_request()

    service.recommend(request)
    assert service.reserve_warmup(request) is True

    service.warm_cache(request)

    response = service.recommend(request)

    assert response.source == "fallback"
    assert gemini_service.call_count == 1
    assert service.reserve_warmup(request) is False
