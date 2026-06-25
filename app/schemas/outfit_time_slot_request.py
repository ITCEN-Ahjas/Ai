from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.outfit_request import (
    CurrentWeatherRequest,
    FeelsLikeWeatherRequest,
)

TimeSlot = Literal["morning", "daytime", "afternoon", "evening"]

TIME_SLOT_ORDER = {
    "morning": 0,
    "daytime": 1,
    "afternoon": 2,
    "evening": 3,
}


class ResidenceWeatherRequest(BaseModel):
    city: str = Field(min_length=1, max_length=80)
    country: str = Field(min_length=1, max_length=80)
    feelsLikeTemperature: float = Field(
        description="현재 거주 도시의 현재 체감온도",
    )

    @field_validator("city", "country")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("현재 거주 도시 정보는 비워둘 수 없습니다.")

        return normalized_value


class TimeSlotWeatherRequest(BaseModel):
    timeSlot: TimeSlot
    timeSlotName: str = Field(min_length=1, max_length=20)
    forecastAt: datetime
    startTime: time
    endTime: time
    currentWeather: CurrentWeatherRequest
    feelsLikeWeather: FeelsLikeWeatherRequest

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.startTime >= self.endTime:
            raise ValueError("시간대 시작 시각은 종료 시각보다 빨라야 합니다.")

        return self


class TimeSlotOutfitRecommendationRequest(BaseModel):
    region: str = Field(
        min_length=1,
        max_length=20,
        description="선택한 충북 지역",
    )
    residenceWeather: ResidenceWeatherRequest | None = Field(
        default=None,
        description="현재 거주 도시의 현재 체감온도 정보",
    )
    timeSlots: list[TimeSlotWeatherRequest] = Field(
        min_length=1,
        max_length=4,
        description="현재 시각 이후 시간대별 충북 날씨",
    )

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("지역명은 비워둘 수 없습니다.")

        return normalized_value

    @model_validator(mode="after")
    def validate_time_slots(self):
        time_slot_codes = [item.timeSlot for item in self.timeSlots]

        if len(time_slot_codes) != len(set(time_slot_codes)):
            raise ValueError("동일한 시간대가 중복되었습니다.")

        ordered_codes = sorted(
            time_slot_codes,
            key=lambda code: TIME_SLOT_ORDER[code],
        )

        if time_slot_codes != ordered_codes:
            raise ValueError(
                "시간대는 아침, 낮, 오후, 저녁 순서로 전달해야 합니다."
            )

        return self
