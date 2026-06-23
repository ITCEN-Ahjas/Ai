from typing import Literal

from pydantic import BaseModel, Field, field_validator


class OutfitCard(BaseModel):
    code: str = Field(pattern=r"^[a-z_]+$")
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


class OutfitSelection(BaseModel):
    outerwearCode: str = Field(pattern=r"^[a-z_]+$")
    topCode: str = Field(pattern=r"^[a-z_]+$")
    bottomCode: str = Field(pattern=r"^[a-z_]+$")
    shoesCode: str = Field(pattern=r"^[a-z_]+$")
    preparationCodes: list[str] = Field(min_length=1, max_length=4)

    @field_validator("preparationCodes")
    @classmethod
    def normalize_preparation_codes(cls, values: list[str]) -> list[str]:
        normalized_values: list[str] = []

        for value in values:
            normalized_value = value.strip().lower()

            if not normalized_value:
                raise ValueError("준비물 코드는 비워둘 수 없습니다.")

            if normalized_value not in normalized_values:
                normalized_values.append(normalized_value)

        if not normalized_values:
            raise ValueError("준비물은 최소 1개 이상 선택해야 합니다.")

        return normalized_values


class OutfitRecommendationResponse(BaseModel):
    region: str
    travelStyle: str
    source: Literal["ai", "fallback"] = "fallback"
    outfitCards: OutfitCards
    preparationItems: list[PreparationItem] = Field(
        min_length=1,
        max_length=4,
    )