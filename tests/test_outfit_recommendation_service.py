from app.schemas.outfit_batch_request import OutfitBatchRecommendationRequest
from app.schemas.outfit_batch_response import (TRAVEL_STYLES,
                                               BatchOutfitSelection)
from app.schemas.outfit_request import (CurrentWeatherRequest,
                                        FeelsLikeWeatherRequest,
                                        OutfitRecommendationRequest)
from app.schemas.outfit_response import OutfitSelection
from app.services.gemini_outfit_service import GeminiOutfitGenerationError
from app.services.outfit_recommendation_service import \
    OutfitRecommendationService
from app.services.outfit_rule_engine import OutfitRuleEngine


class FakeGeminiSuccessService:
    def generate(
        self,
        request: OutfitRecommendationRequest,
        fallback_selection: OutfitSelection,
    ) -> OutfitSelection:
        return OutfitSelection(
            outerwearCode="waterproof_jacket",
            topCode="long_sleeve_tshirt",
            bottomCode="water_repellent_pants",
            shoesCode="waterproof_hiking_shoes",
            preparationCodes=[
                "umbrella",
                "waterproof_pouch",
                "water_bottle",
            ],
        )


class FakeGeminiFailureService:
    def generate(
        self,
        request: OutfitRecommendationRequest,
        fallback_selection: OutfitSelection,
    ) -> OutfitSelection:
        raise GeminiOutfitGenerationError("Gemini 호출 실패")


class FakeGeminiInvalidSelectionService:
    def generate(
        self,
        request: OutfitRecommendationRequest,
        fallback_selection: OutfitSelection,
    ) -> OutfitSelection:
        return OutfitSelection(
            outerwearCode="not_supported",
            topCode="long_sleeve_tshirt",
            bottomCode="cotton_pants",
            shoesCode="sneakers",
            preparationCodes=["water_bottle"],
        )


class FakeGeminiBatchSuccessService:
    def generate_batch(
        self,
        request: OutfitBatchRecommendationRequest,
        fallback_selections: dict[str, OutfitSelection],
    ) -> BatchOutfitSelection:
        return BatchOutfitSelection(
            basic=fallback_selections["기본 추천"],
            walking=OutfitSelection(
                outerwearCode="windbreaker",
                topCode="long_sleeve_tshirt",
                bottomCode="jogger_pants",
                shoesCode="cushioned_sneakers",
                preparationCodes=["water_bottle", "battery"],
            ),
            outdoor=OutfitSelection(
                outerwearCode="windbreaker",
                topCode="long_sleeve_tshirt",
                bottomCode="training_pants",
                shoesCode="grip_sneakers",
                preparationCodes=[
                    "hat",
                    "water_bottle",
                    "insect_repellent",
                ],
            ),
            indoor=OutfitSelection(
                outerwearCode="light_cardigan",
                topCode="long_sleeve_tshirt",
                bottomCode="cotton_pants",
                shoesCode="sneakers",
                preparationCodes=["light_outerwear", "battery"],
            ),
            night=OutfitSelection(
                outerwearCode="light_jacket",
                topCode="long_sleeve_tshirt",
                bottomCode="jeans",
                shoesCode="sneakers",
                preparationCodes=["light_outerwear", "battery"],
            ),
            rainy=OutfitSelection(
                outerwearCode="waterproof_jacket",
                topCode="long_sleeve_tshirt",
                bottomCode="water_repellent_pants",
                shoesCode="rain_boots",
                preparationCodes=[
                    "umbrella",
                    "waterproof_pouch",
                    "extra_socks",
                ],
            ),
        )


class FakeGeminiBatchFailureService:
    def generate_batch(
        self,
        request: OutfitBatchRecommendationRequest,
        fallback_selections: dict[str, OutfitSelection],
    ) -> BatchOutfitSelection:
        raise GeminiOutfitGenerationError("Gemini 배치 호출 실패")


def create_current_weather(
    *,
    temperature: float = 16.2,
    precipitation_amount: str = "강수 없음",
    precipitation_type: str = "없음",
    precipitation_probability: int = 20,
    weather_condition: str = "흐림",
    sky_status: str = "흐림",
) -> CurrentWeatherRequest:
    return CurrentWeatherRequest(
        temperature=temperature,
        humidity=70,
        windSpeed=4.5,
        windStatus="보통 바람",
        precipitationAmount=precipitation_amount,
        precipitationType=precipitation_type,
        precipitationProbability=precipitation_probability,
        skyStatus=sky_status,
        weatherCondition=weather_condition,
    )


def create_feels_like_weather(
    *,
    temperature: float = 16.2,
    feels_like_temperature: float = 14.8,
) -> FeelsLikeWeatherRequest:
    return FeelsLikeWeatherRequest(
        feelsLikeTemperature=feels_like_temperature,
        temperatureDifference=feels_like_temperature - temperature,
        description="바람으로 실제 기온보다 쌀쌀하게 느껴집니다.",
        factors=["바람"],
    )


def create_request(
    *,
    travel_style: str = "많이 걷는 여행",
    temperature: float = 16.2,
    feels_like_temperature: float = 14.8,
    precipitation_amount: str = "강수 없음",
    precipitation_type: str = "없음",
    precipitation_probability: int = 20,
    weather_condition: str = "흐림",
    sky_status: str = "흐림",
) -> OutfitRecommendationRequest:
    return OutfitRecommendationRequest(
        region="청주",
        travelStyle=travel_style,
        currentWeather=create_current_weather(
            temperature=temperature,
            precipitation_amount=precipitation_amount,
            precipitation_type=precipitation_type,
            precipitation_probability=precipitation_probability,
            weather_condition=weather_condition,
            sky_status=sky_status,
        ),
        feelsLikeWeather=create_feels_like_weather(
            temperature=temperature,
            feels_like_temperature=feels_like_temperature,
        ),
    )


def create_batch_request(
    *,
    temperature: float = 16.2,
    feels_like_temperature: float = 14.8,
    precipitation_amount: str = "강수 없음",
    precipitation_type: str = "없음",
    precipitation_probability: int = 20,
    weather_condition: str = "흐림",
    sky_status: str = "흐림",
) -> OutfitBatchRecommendationRequest:
    return OutfitBatchRecommendationRequest(
        region="청주",
        currentWeather=create_current_weather(
            temperature=temperature,
            precipitation_amount=precipitation_amount,
            precipitation_type=precipitation_type,
            precipitation_probability=precipitation_probability,
            weather_condition=weather_condition,
            sky_status=sky_status,
        ),
        feelsLikeWeather=create_feels_like_weather(
            temperature=temperature,
            feels_like_temperature=feels_like_temperature,
        ),
    )


def test_returns_catalog_copy_when_gemini_selection_succeeds() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiSuccessService(),
    )

    response = service.recommend(create_request())

    assert response.source == "ai"
    assert response.outfitCards.outerwear.code == "waterproof_jacket"
    assert response.outfitCards.outerwear.name == "방수 재킷 / 우비"
    assert (
        response.outfitCards.outerwear.description
        == "비가 오는 날 옷이 젖는 것을 줄여줘요."
    )
    assert response.outfitCards.shoes.code == "waterproof_hiking_shoes"
    assert response.outfitCards.shoes.name == "방수 트레킹화"
    assert len(response.preparationItems) == 3


def test_returns_catalog_fallback_when_gemini_generation_fails() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiFailureService(),
    )

    response = service.recommend(create_request())

    assert response.source == "fallback"
    assert response.outfitCards.outerwear.code == "light_jacket"
    assert response.outfitCards.outerwear.name == "얇은 점퍼 / 가벼운 재킷"
    assert (
        response.outfitCards.outerwear.description
        == "선선한 날씨와 일교차에 대응하기 좋아요."
    )
    assert 1 <= len(response.preparationItems) <= 4


def test_returns_fallback_when_gemini_returns_unknown_catalog_code() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiInvalidSelectionService(),
    )

    response = service.recommend(create_request())

    assert response.source == "fallback"
    assert response.outfitCards.outerwear.code == "light_jacket"


def test_recommends_rain_boots_when_it_is_actually_raining() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiFailureService(),
    )

    response = service.recommend(
        create_request(
            travel_style="비 오는 날 대비",
            precipitation_amount="강한 비",
            precipitation_type="비",
            precipitation_probability=90,
            weather_condition="비",
            sky_status="흐림",
        )
    )

    assert response.outfitCards.outerwear.code == "waterproof_jacket"
    assert response.outfitCards.shoes.code == "rain_boots"
    assert response.outfitCards.shoes.name == "짧은 장화 / 레인부츠"
    assert {item.code for item in response.preparationItems}.issuperset(
        {"umbrella", "waterproof_pouch"}
    )


def test_recommends_cushioned_sneakers_for_walking_without_rain() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiFailureService(),
    )

    response = service.recommend(
        create_request(travel_style="많이 걷는 여행")
    )

    assert response.outfitCards.shoes.code == "cushioned_sneakers"
    assert response.outfitCards.shoes.name == "쿠션 운동화"


def test_limits_preparation_items_to_four_and_removes_duplicates() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiFailureService(),
    )

    response = service.recommend(
        create_request(
            travel_style="야외 활동",
            temperature=31.0,
            feels_like_temperature=31.0,
        )
    )

    preparation_codes = [item.code for item in response.preparationItems]

    assert len(preparation_codes) <= 4
    assert len(preparation_codes) == len(set(preparation_codes))


def test_returns_six_styles_when_batch_gemini_generation_succeeds() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiBatchSuccessService(),
    )

    response = service.recommend_batch(create_batch_request())

    assert response.source == "ai"
    assert set(response.recommendations.keys()) == set(TRAVEL_STYLES)
    assert len(response.recommendations) == 6

    walking = response.recommendations["많이 걷는 여행"]
    rainy = response.recommendations["비 오는 날 대비"]

    assert walking.outfitCards.shoes.code == "cushioned_sneakers"
    assert rainy.outfitCards.outerwear.code == "waterproof_jacket"
    assert rainy.outfitCards.shoes.code == "rain_boots"


def test_returns_six_fallback_styles_when_batch_gemini_fails() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiBatchFailureService(),
    )

    response = service.recommend_batch(
        create_batch_request(
            precipitation_amount="강한 비",
            precipitation_type="비",
            precipitation_probability=90,
            weather_condition="비",
            sky_status="흐림",
        )
    )

    assert response.source == "fallback"
    assert set(response.recommendations.keys()) == set(TRAVEL_STYLES)
    assert len(response.recommendations) == 6

    rainy = response.recommendations["비 오는 날 대비"]
    walking = response.recommendations["많이 걷는 여행"]

    assert rainy.outfitCards.shoes.code == "rain_boots"
    assert walking.outfitCards.shoes.code == "waterproof_hiking_shoes"


def test_returns_four_outfit_cards_for_each_batch_style() -> None:
    service = OutfitRecommendationService(
        rule_engine=OutfitRuleEngine(),
        gemini_outfit_service=FakeGeminiBatchFailureService(),
    )

    response = service.recommend_batch(create_batch_request())

    for recommendation in response.recommendations.values():
        assert recommendation.outfitCards.outerwear.code
        assert recommendation.outfitCards.top.code
        assert recommendation.outfitCards.bottom.code
        assert recommendation.outfitCards.shoes.code
        assert 1 <= len(recommendation.preparationItems) <= 4