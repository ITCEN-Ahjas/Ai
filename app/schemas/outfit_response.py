from typing import Literal

from pydantic import BaseModel, Field


class OutfitRecommendationResponse(BaseModel):
    region: str
    travelStyle: str
    source: Literal["rule"] = "rule"
    summary: str

    outerwear: list[str] = Field(description="아우터 추천")
    tops: list[str] = Field(description="상의 추천")
    bottoms: list[str] = Field(description="하의 추천")
    shoes: list[str] = Field(description="신발 추천")
    preparationItems: list[str] = Field(description="준비물 추천")
    reasons: list[str] = Field(description="추천 이유")