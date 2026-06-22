from app.schemas.outfit_request import (CurrentWeatherRequest,
                                        FeelsLikeWeatherRequest,
                                        OutfitRecommendationRequest)
from app.schemas.outfit_response import (GeminiOutfitCopy,
                                         GeminiPreparationDescription)
from app.services.gemini_outfit_service import GeminiOutfitGenerationError
from app.services.outfit_recommendation_service import \
    OutfitRecommendationService
from app.services.outfit_rule_engine import OutfitRuleEngine


class FakeGeminiSuccessService:
    def generate(
        self,
        request: OutfitRecommendationRequest,
        fallback,
    ) -> GeminiOutfitCopy:
        return GeminiOutfitCopy(
            outerwearDescription="체감온도 변화에 대비해 가볍게 걸치기 좋아요.",
            topDescription="여행 중 편안하게 입을 수 있는 기본 상의예요.",
            bottomDescription="오래 이동해도 활동하기 편한 하의예요.",
            shoesDescription="장시간 걷는 일정에 편안한 신발이에요.",
            preparationDescriptions=[
                GeminiPreparationDescription(
                    code="water_bottle",
                    description="여행 중 수분 보충을 위해 챙기세요.",
                )
            ],
        )


class FakeGeminiFailureService:
    def generate(
        self,
        request: OutfitRecommendationRequest,
        fallback,
    ) -> GeminiOutfitCopy:
        raise GeminiOutfitGenerationError("Gemini 호출 실패")


def create_request() -> OutfitRecommendationRequest:
    return OutfitRecommendationRequest(
        region="청주",
        travelStyle="많이 걷는 여행",
        currentWeather=CurrentWeatherRequest(
            temperature=16.2,
            humidity=70,
            windSpeed=4.5,
            windStatus="보통 바람",
            precipitationAmount="강수 없음",
            precipitationType="없음",
            precipitationProbability=20,
            skyStatus="흐림",
            weatherCondition="흐림",
        ),
        feelsLikeWeather=FeelsLikeWeatherRequest(
            feelsLikeTemperature=14.8,
            temperatureDifference=-1.4,
            description="바람으로 실제 기온보다 쌀쌀하게 느껴집니다.",
            factors=["바람"],
        ),
    )


def test_returns_ai_copy_when_gemini_generation_succeeds() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiSuccessService(),
    )

    response = service.recommend(create_request())

    assert response.source == "ai"
    assert response.outfitCards.outerwear.name
    assert "체감온도" in response.outfitCards.outerwear.description
    assert any(
        item.description == "여행 중 수분 보충을 위해 챙기세요."
        for item in response.preparationItems
        if item.code == "water_bottle"
    )


def test_returns_fallback_when_gemini_generation_fails() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiFailureService(),
    )

    response = service.recommend(create_request())

    assert response.source == "fallback"
    assert response.outfitCards.outerwear.name
    assert 1 <= len(response.preparationItems) <= 4