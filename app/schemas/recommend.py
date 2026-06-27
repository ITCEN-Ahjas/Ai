from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Interest = Literal[
    "nature",
    "food",
    "exhibition",
    "activity",
    "shopping",
    "festival",
    "cafe",
]

CompanionType = Literal["solo", "couple", "family", "friends"]
BudgetLevel = Literal["low", "medium", "high"]
ActivityPace = Literal["relaxed", "balanced", "tight"]
TransportMode = Literal["walk", "public_transport", "car", "taxi"]
PlaceCategory = Literal[
    "nature",
    "restaurant",
    "cafe",
    "museum",
    "experience",
    "shopping",
    "festival",
    "landmark",
]
WeatherCondition = Literal[
    "clear",
    "cloudy",
    "rain",
    "snow",
    "heat",
    "cold",
    "dust",
]
RouteSource = Literal["ai", "fallback"]


class UserPreference(BaseModel):
    interests: list[Interest] = Field(min_length=1, max_length=5)
    companionType: CompanionType
    budgetLevel: BudgetLevel = "medium"
    activityPace: ActivityPace = "balanced"
    transportMode: TransportMode = "public_transport"

    @field_validator("interests")
    @classmethod
    def normalize_interests(cls, values: list[Interest]) -> list[Interest]:
        normalized_values: list[Interest] = []

        for value in values:
            if value not in normalized_values:
                normalized_values.append(value)

        return normalized_values


class TravelConstraint(BaseModel):
    travelDate: date
    startTime: time
    endTime: time
    startLocation: str = Field(min_length=1, max_length=80)
    endLocation: str | None = Field(default=None, min_length=1, max_length=80)

    @field_validator("startLocation", "endLocation")
    @classmethod
    def normalize_location(cls, value: str | None) -> str | None:
        if value is None:
            return value

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("location must not be blank")

        return normalized_value

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.startTime >= self.endTime:
            raise ValueError("startTime must be earlier than endTime")

        return self


class HourlyWeather(BaseModel):
    time: time
    condition: WeatherCondition
    precipitationProbability: int = Field(ge=0, le=100)
    temperature: float
    feelsLikeTemperature: float
    fineDustLevel: Literal["good", "normal", "bad", "very_bad"] = "normal"


class CandidatePlace(BaseModel):
    placeId: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    category: PlaceCategory
    interests: list[Interest] = Field(min_length=1, max_length=5)
    indoor: bool
    address: str | None = Field(default=None, max_length=120)
    imageUrl: str | None = Field(default=None, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    averageStayMinutes: int = Field(default=90, ge=30, le=240)
    openTime: time | None = None
    closeTime: time | None = None

    @field_validator("placeId", "name", "address", "imageUrl")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return value

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("text value must not be blank")

        return normalized_value

    @field_validator("interests")
    @classmethod
    def normalize_interests(cls, values: list[Interest]) -> list[Interest]:
        normalized_values: list[Interest] = []

        for value in values:
            if value not in normalized_values:
                normalized_values.append(value)

        return normalized_values

    @model_validator(mode="after")
    def validate_opening_hours(self):
        if (
            self.openTime is not None
            and self.closeTime is not None
            and self.openTime >= self.closeTime
        ):
            raise ValueError("openTime must be earlier than closeTime")

        return self


class RouteRecommendationRequest(BaseModel):
    region: str = Field(min_length=1, max_length=20)
    preference: UserPreference
    constraint: TravelConstraint
    weatherTimeline: list[HourlyWeather] = Field(min_length=1, max_length=24)
    candidatePlaces: list[CandidatePlace] = Field(min_length=1, max_length=30)

    @field_validator("region")
    @classmethod
    def normalize_region(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("region must not be blank")

        return normalized_value


class RoutePlace(BaseModel):
    day: int = Field(default=1, ge=1, le=30)
    order: int = Field(default=1, ge=1, le=100)
    placeId: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    category: PlaceCategory
    startTime: time
    endTime: time
    indoor: bool
    address: str | None = Field(default=None, max_length=120)
    imageUrl: str | None = Field(default=None, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    recommendationReason: str = Field(min_length=1, max_length=160)
    weatherReason: str = Field(min_length=1, max_length=160)
    moveTip: str | None = Field(default=None, max_length=160)

    @field_validator("placeId", "name", "address", "imageUrl")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return value

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("text value must not be blank")

        return normalized_value

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.startTime >= self.endTime:
            raise ValueError("startTime must be earlier than endTime")

        return self


class PlanBOption(BaseModel):
    triggerCondition: str = Field(min_length=1, max_length=120)
    replaceFrom: str = Field(min_length=1, max_length=80)
    replaceTo: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1, max_length=160)


class WeatherNote(BaseModel):
    timeRange: str = Field(min_length=1, max_length=40)
    summary: str = Field(min_length=1, max_length=160)
    cautionLevel: Literal["low", "medium", "high"] = "low"


class RouteOverview(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    region: str = Field(min_length=1, max_length=20)
    totalPlaces: int = Field(ge=1, le=30)
    totalStayMinutes: int = Field(ge=1, le=1440)
    startLocation: str = Field(min_length=1, max_length=80)
    endLocation: str | None = Field(default=None, min_length=1, max_length=80)
    styleTags: list[str] = Field(min_length=1, max_length=6)
    weatherSummary: str = Field(min_length=1, max_length=180)

    @field_validator("title", "region", "startLocation", "endLocation")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return value

        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("text value must not be blank")

        return normalized_value

    @field_validator("styleTags")
    @classmethod
    def normalize_style_tags(cls, values: list[str]) -> list[str]:
        normalized_values: list[str] = []

        for value in values:
            normalized_value = value.strip()

            if not normalized_value:
                raise ValueError("style tag must not be blank")

            if normalized_value not in normalized_values:
                normalized_values.append(normalized_value)

        return normalized_values


class RouteRecommendationResponse(BaseModel):
    region: str
    source: RouteSource = "fallback"
    summary: str = Field(min_length=1, max_length=220)
    routeOverview: RouteOverview
    itinerary: list[RoutePlace] = Field(min_length=1, max_length=8)
    planB: list[PlanBOption] = Field(default_factory=list, max_length=3)
    weatherNotes: list[WeatherNote] = Field(default_factory=list, max_length=5)
