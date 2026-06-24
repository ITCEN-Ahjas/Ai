from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.outfit_time_slot_request import (
    TimeSlotOutfitRecommendationRequest,
)


def create_time_slot(
    *,
    time_slot: str,
    time_slot_name: str,
    forecast_at: str,
    start_time: str,
    end_time: str,
) -> dict:
    return {
        "timeSlot": time_slot,
        "timeSlotName": time_slot_name,
        "forecastAt": forecast_at,
        "startTime": start_time,
        "endTime": end_time,
        "currentWeather": {
            "temperature": 23.0,
            "humidity": 70,
            "windSpeed": 1.5,
            "windStatus": "약함",
            "precipitationAmount": "강수 없음",
            "precipitationType": "강수 없음",
            "precipitationProbability": 10,
            "skyStatus": "맑음",
            "weatherCondition": "맑음",
        },
        "feelsLikeWeather": {
            "feelsLikeTemperature": 23.0,
            "temperatureDifference": 0.0,
            "description": "현재 기온과 비슷하게 느껴집니다.",
            "factors": ["현재 기온"],
        },
    }


def create_request_data() -> dict:
    return {
        "region": "청주",
        "timeSlots": [
            create_time_slot(
                time_slot="afternoon",
                time_slot_name="오후",
                forecast_at="2026-06-24T15:00:00",
                start_time="14:00",
                end_time="17:00",
            ),
            create_time_slot(
                time_slot="evening",
                time_slot_name="저녁",
                forecast_at="2026-06-24T19:00:00",
                start_time="17:00",
                end_time="21:00",
            ),
        ],
    }


def test_time_slot_request_accepts_remaining_time_slots() -> None:
    request = TimeSlotOutfitRecommendationRequest(**create_request_data())

    assert request.region == "청주"
    assert request.residenceWeather is None
    assert len(request.timeSlots) == 2
    assert request.timeSlots[0].timeSlot == "afternoon"
    assert request.timeSlots[1].forecastAt == datetime(
        2026,
        6,
        24,
        19,
        0,
    )


def test_time_slot_request_accepts_residence_weather() -> None:
    request_data = create_request_data()
    request_data["residenceWeather"] = {
        "city": " New York ",
        "country": " United States ",
        "feelsLikeTemperature": -5.0,
    }

    request = TimeSlotOutfitRecommendationRequest(**request_data)

    assert request.residenceWeather is not None
    assert request.residenceWeather.city == "New York"
    assert request.residenceWeather.country == "United States"
    assert request.residenceWeather.feelsLikeTemperature == -5.0


def test_time_slot_request_rejects_duplicate_time_slot() -> None:
    with pytest.raises(ValidationError):
        TimeSlotOutfitRecommendationRequest(
            region="청주",
            timeSlots=[
                create_time_slot(
                    time_slot="afternoon",
                    time_slot_name="오후",
                    forecast_at="2026-06-24T15:00:00",
                    start_time="14:00",
                    end_time="17:00",
                ),
                create_time_slot(
                    time_slot="afternoon",
                    time_slot_name="오후",
                    forecast_at="2026-06-24T16:00:00",
                    start_time="14:00",
                    end_time="17:00",
                ),
            ],
        )


def test_time_slot_request_rejects_unordered_time_slots() -> None:
    with pytest.raises(ValidationError):
        TimeSlotOutfitRecommendationRequest(
            region="청주",
            timeSlots=[
                create_time_slot(
                    time_slot="evening",
                    time_slot_name="저녁",
                    forecast_at="2026-06-24T19:00:00",
                    start_time="17:00",
                    end_time="21:00",
                ),
                create_time_slot(
                    time_slot="afternoon",
                    time_slot_name="오후",
                    forecast_at="2026-06-24T15:00:00",
                    start_time="14:00",
                    end_time="17:00",
                ),
            ],
        )
