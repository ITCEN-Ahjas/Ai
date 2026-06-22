from typing import Literal

from pydantic import BaseModel, Field


class OutfitCard(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    description: str = Field(min_length=1, max_length=100)


class OutfitCards(BaseModel):
    outerwear: OutfitCard
    top: OutfitCard
    bottom: OutfitCard
    shoes: OutfitCard


class PreparationItem(BaseModel):
    code: str = Field(pattern=r"^[a-z_]+$")
    name: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=100)


class GeminiPreparationDescription(BaseModel):
    code: str = Field(pattern=r"^[a-z_]+$")
    description: str = Field(min_length=1, max_length=100)


class GeminiOutfitCopy(BaseModel):
    outerwearDescription: str = Field(min_length=1, max_length=100)
    topDescription: str = Field(min_length=1, max_length=100)
    bottomDescription: str = Field(min_length=1, max_length=100)
    shoesDescription: str = Field(min_length=1, max_length=100)
    preparationDescriptions: list[GeminiPreparationDescription] = Field(
        default_factory=list,
        max_length=4,
    )


class OutfitRecommendationResponse(BaseModel):
    region: str
    travelStyle: str
    source: Literal["ai", "fallback"] = "fallback"
    outfitCards: OutfitCards
    preparationItems: list[PreparationItem] = Field(
        min_length=1,
        max_length=4,
    )