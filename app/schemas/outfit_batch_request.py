from pydantic import BaseModel, Field, field_validator

from app.schemas.outfit_request import (CurrentWeatherRequest,
                                        FeelsLikeWeatherRequest)


class OutfitBatchRecommendationRequest(BaseModel):
    region: str = Field(
        min_length=1,
        max_length=20,
        description="선택한 충북 지역",
    )
    currentWeather: CurrentWeatherRequest
    feelsLikeWeather: FeelsLikeWeatherRequest

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("지역명은 비워둘 수 없습니다.")

        return normalized_value