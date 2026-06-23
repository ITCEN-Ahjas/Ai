from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.outfit_response import (OutfitRecommendationResponse,
                                         OutfitSelection)

TRAVEL_STYLE_FIELDS = {
    "기본 추천": "basic",
    "많이 걷는 여행": "walking",
    "야외 활동": "outdoor",
    "실내 중심": "indoor",
    "야간 일정": "night",
    "비 오는 날 대비": "rainy",
}

TRAVEL_STYLES = tuple(TRAVEL_STYLE_FIELDS.keys())


class BatchOutfitSelection(BaseModel):
    basic: OutfitSelection
    walking: OutfitSelection
    outdoor: OutfitSelection
    indoor: OutfitSelection
    night: OutfitSelection
    rainy: OutfitSelection

    def to_style_selections(self) -> dict[str, OutfitSelection]:
        return {
            "기본 추천": self.basic,
            "많이 걷는 여행": self.walking,
            "야외 활동": self.outdoor,
            "실내 중심": self.indoor,
            "야간 일정": self.night,
            "비 오는 날 대비": self.rainy,
        }


class OutfitBatchRecommendationResponse(BaseModel):
    region: str
    source: Literal["ai", "fallback"] = "fallback"
    recommendations: dict[str, OutfitRecommendationResponse] = Field(
        min_length=6,
        max_length=6,
    )

    @model_validator(mode="after")
    def validate_recommendations(self):
        recommendation_styles = set(self.recommendations.keys())
        required_styles = set(TRAVEL_STYLES)

        missing_styles = required_styles - recommendation_styles
        extra_styles = recommendation_styles - required_styles

        if missing_styles:
            raise ValueError(
                f"누락된 여행 스타일 추천이 있습니다: {sorted(missing_styles)}"
            )

        if extra_styles:
            raise ValueError(
                f"지원하지 않는 여행 스타일 추천이 있습니다: {sorted(extra_styles)}"
            )

        return self