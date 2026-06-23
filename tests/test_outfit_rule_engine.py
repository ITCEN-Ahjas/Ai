import pytest

from app.schemas.outfit_request import (CurrentWeatherRequest,
                                        FeelsLikeWeatherRequest,
                                        OutfitRecommendationRequest)
from app.services.outfit_rule_engine import OutfitRuleEngine

rule_engine = OutfitRuleEngine()

TRAVEL_STYLES = [
    "기본 추천",
    "많이 걷는 여행",
    "야외 활동",
    "실내 중심",
    "야간 일정",
    "비 오는 날 대비",
]

FEELS_LIKE_TEMPERATURES = [30, 20, 10, 0]

SCENARIOS = [
    (feels_like_temperature, travel_style)
    for feels_like_temperature in FEELS_LIKE_TEMPERATURES
    for travel_style in TRAVEL_STYLES
]


def create_request(
    feels_like_temperature: float,
    travel_style: str = "기본 추천",
    precipitation_type: str = "없음",
    precipitation_probability: int = 0,
    wind_speed: float = 1.5,
    wind_status: str = "약한 바람",
) -> OutfitRecommendationRequest:
    return OutfitRecommendationRequest(
        region="청주",
        travelStyle=travel_style,
        currentWeather=CurrentWeatherRequest(
            temperature=feels_like_temperature,
            humidity=50,
            windSpeed=wind_speed,
            windStatus=wind_status,
            precipitationAmount="강수 없음",
            precipitationType=precipitation_type,
            precipitationProbability=precipitation_probability,
            skyStatus="맑음",
            weatherCondition=precipitation_type,
        ),
        feelsLikeWeather=FeelsLikeWeatherRequest(
            feelsLikeTemperature=feels_like_temperature,
            temperatureDifference=0,
            description="테스트 체감 날씨",
            factors=[],
        ),
    )


@pytest.mark.parametrize(
    ("feels_like_temperature", "travel_style"),
    SCENARIOS,
)
def test_recommendation_is_created_for_weather_and_style_scenarios(
    feels_like_temperature: float,
    travel_style: str,
) -> None:
    response = rule_engine.recommend(
        create_request(
            feels_like_temperature=feels_like_temperature,
            travel_style=travel_style,
        )
    )

    assert response.region == "청주"
    assert response.travelStyle == travel_style
    assert response.source == "fallback"
    assert response.outfitCards.outerwear.name
    assert response.outfitCards.top.name
    assert response.outfitCards.bottom.name
    assert response.outfitCards.shoes.name
    assert 1 <= len(response.preparationItems) <= 4


def test_rain_weather_includes_waterproof_cards_and_umbrella() -> None:
    response = rule_engine.recommend(
        create_request(
            feels_like_temperature=12,
            precipitation_type="비",
            precipitation_probability=80,
        )
    )

    assert "방수" in response.outfitCards.outerwear.name
    assert response.outfitCards.shoes.code == "rain_boots"
    assert any(item.code == "umbrella" for item in response.preparationItems)


def test_snow_weather_includes_winter_shoes_and_warm_items() -> None:
    response = rule_engine.recommend(
        create_request(
            feels_like_temperature=1,
            precipitation_type="눈",
            precipitation_probability=70,
        )
    )

    assert "방한" in response.outfitCards.outerwear.name
    assert "미끄럼" in response.outfitCards.shoes.name
    assert any(item.code == "warm_accessory" for item in response.preparationItems)


def test_strong_wind_recommends_windbreaker() -> None:
    response = rule_engine.recommend(
        create_request(
            feels_like_temperature=14,
            wind_speed=9,
            wind_status="강한 바람",
        )
    )

    assert "바람막이" in response.outfitCards.outerwear.name


def test_walking_travel_recommends_comfortable_shoes() -> None:
    response = rule_engine.recommend(
        create_request(
            feels_like_temperature=18,
            travel_style="많이 걷는 여행",
        )
    )

    assert "운동화" in response.outfitCards.shoes.name
    assert any(
        item.code == "comfortable_shoes"
        for item in response.preparationItems
    )


def test_rainy_day_style_includes_umbrella_without_rain_data() -> None:
    response = rule_engine.recommend(
        create_request(
            feels_like_temperature=18,
            travel_style="비 오는 날 대비",
        )
    )

    assert "방수" in response.outfitCards.outerwear.name
    assert any(item.code == "umbrella" for item in response.preparationItems)
