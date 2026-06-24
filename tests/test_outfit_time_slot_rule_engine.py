from app.schemas.outfit_time_slot_request import TimeSlotWeatherRequest
from app.services.outfit_time_slot_rule_engine import TimeSlotOutfitRuleEngine


def create_time_slot_weather(
    *,
    time_slot: str = "afternoon",
    time_slot_name: str = "오후",
    temperature: float = 23.0,
    feels_like_temperature: float = 23.0,
    precipitation_amount: str = "강수 없음",
    precipitation_type: str = "강수 없음",
    precipitation_probability: int = 10,
    weather_condition: str = "맑음",
) -> TimeSlotWeatherRequest:
    return TimeSlotWeatherRequest(
        timeSlot=time_slot,
        timeSlotName=time_slot_name,
        forecastAt="2026-06-24T15:00:00",
        startTime="14:00",
        endTime="17:00",
        currentWeather={
            "temperature": temperature,
            "humidity": 65,
            "windSpeed": 1.5,
            "windStatus": "약함",
            "precipitationAmount": precipitation_amount,
            "precipitationType": precipitation_type,
            "precipitationProbability": precipitation_probability,
            "skyStatus": "맑음",
            "weatherCondition": weather_condition,
        },
        feelsLikeWeather={
            "feelsLikeTemperature": feels_like_temperature,
            "temperatureDifference": feels_like_temperature - temperature,
            "description": "테스트 체감 날씨",
            "factors": [],
        },
    )


def test_rainy_time_slot_recommends_waterproof_cards() -> None:
    response = TimeSlotOutfitRuleEngine().select(
        region="청주",
        time_slot_weather=create_time_slot_weather(
            precipitation_amount="강한 비",
            precipitation_type="비",
            precipitation_probability=90,
            weather_condition="비",
        ),
    )

    assert response.outerwearCode == "waterproof_jacket"
    assert response.shoesCode == "rain_boots"
    assert "umbrella" in response.preparationCodes


def test_evening_time_slot_adds_light_jacket_and_battery() -> None:
    response = TimeSlotOutfitRuleEngine().select(
        region="청주",
        time_slot_weather=create_time_slot_weather(
            time_slot="evening",
            time_slot_name="저녁",
            temperature=21.0,
            feels_like_temperature=20.0,
        ),
    )

    assert response.outerwearCode == "light_jacket"
    assert "battery" in response.preparationCodes


def test_hot_daytime_uses_lightweight_outfit() -> None:
    response = TimeSlotOutfitRuleEngine().select(
        region="청주",
        time_slot_weather=create_time_slot_weather(
            time_slot="daytime",
            time_slot_name="낮",
            temperature=31.0,
            feels_like_temperature=31.0,
        ),
    )

    assert response.outerwearCode == "no_outer"
    assert response.topCode == "short_sleeve_tshirt"
    assert response.bottomCode == "shorts"
