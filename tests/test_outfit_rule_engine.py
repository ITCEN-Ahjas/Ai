import pytest

from app.schemas.outfit_request import (CurrentWeatherRequest,
                                        FeelsLikeWeatherRequest,
                                        OutfitRecommendationRequest)
from app.services.outfit_rule_engine import OutfitRuleEngine

rule_engine = OutfitRuleEngine()

TRAVEL_STYLES = ["관광", "축제", "레포츠", "자연 탐방"]
FEELS_LIKE_TEMPERATURES = [30, 24, 18, 12, 2]

SCENARIOS = [
    (feels_like_temperature, travel_style)
    for feels_like_temperature in FEELS_LIKE_TEMPERATURES
    for travel_style in TRAVEL_STYLES
]


def create_request(
    feels_like_temperature: float,
    travel_style: str = "관광",
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
def test_recommendation_is_created_for_twenty_weather_and_style_scenarios(
    feels_like_temperature: float,
    travel_style: str,
) -> None:
    request = create_request(
        feels_like_temperature=feels_like_temperature,
        travel_style=travel_style,
    )

    response = rule_engine.recommend(request)

    assert response.region == "청주"
    assert response.travelStyle == travel_style
    assert response.source == "rule"
    assert len(response.outerwear) > 0
    assert len(response.tops) > 0
    assert len(response.bottoms) > 0
    assert len(response.shoes) > 0
    assert len(response.preparationItems) > 0
    assert len(response.reasons) > 0


def test_rain_weather_includes_waterproof_preparation_items() -> None:
    request = create_request(
        feels_like_temperature=16,
        precipitation_type="비",
        precipitation_probability=80,
    )

    response = rule_engine.recommend(request)

    assert any("우산" in item for item in response.preparationItems)
    assert any("방수" in item for item in response.outerwear)


def test_snow_weather_includes_anti_slip_shoes() -> None:
    request = create_request(
        feels_like_temperature=1,
        precipitation_type="눈",
        precipitation_probability=70,
    )

    response = rule_engine.recommend(request)

    assert any("미끄럼" in item for item in response.shoes)
    assert any("장갑" in item for item in response.preparationItems)


def test_strong_wind_adds_windproof_outerwear() -> None:
    request = create_request(
        feels_like_temperature=14,
        wind_speed=9,
        wind_status="강한 바람",
    )

    response = rule_engine.recommend(request)

    assert any("바람" in item for item in response.outerwear)
    assert any("바람" in reason for reason in response.reasons)


def test_leports_style_adds_activity_friendly_items() -> None:
    request = create_request(
        feels_like_temperature=20,
        travel_style="레포츠",
    )

    response = rule_engine.recommend(request)

    assert any("기능성" in item for item in response.tops)
    assert any("안정적" in item for item in response.shoes)