from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.outfit_response import (
    OutfitCards,
    OutfitSelection,
    PreparationItem,
)
from app.schemas.outfit_time_slot_request import (
    TIME_SLOT_ORDER,
    TimeSlot,
)


class TimeSlotOutfitSelection(OutfitSelection):
    timeSlot: TimeSlot


class TimeSlotOutfitSelectionBatch(BaseModel):
    recommendations: list[TimeSlotOutfitSelection] = Field(
        min_length=1,
        max_length=4,
    )

    @model_validator(mode="after")
    def validate_recommendations(self):
        time_slot_codes = [
            recommendation.timeSlot
            for recommendation in self.recommendations
        ]

        if len(time_slot_codes) != len(set(time_slot_codes)):
            raise ValueError("Gemini 응답에 중복된 시간대가 있습니다.")

        return self

    def to_time_slot_selections(self) -> dict[str, OutfitSelection]:
        return {
            recommendation.timeSlot: OutfitSelection(
                outerwearCode=recommendation.outerwearCode,
                topCode=recommendation.topCode,
                bottomCode=recommendation.bottomCode,
                shoesCode=recommendation.shoesCode,
                preparationCodes=recommendation.preparationCodes,
            )
            for recommendation in self.recommendations
        }


class TimeSlotOutfitRecommendation(BaseModel):
    timeSlot: TimeSlot
    timeSlotName: str = Field(min_length=1, max_length=20)
    forecastAt: datetime
    startTime: time
    endTime: time
    outfitCards: OutfitCards
    preparationItems: list[PreparationItem] = Field(
        min_length=1,
        max_length=4,
    )


class TimeSlotOutfitBatchRecommendationResponse(BaseModel):
    region: str
    source: Literal["ai", "fallback"] = "fallback"
    recommendations: list[TimeSlotOutfitRecommendation] = Field(
        min_length=1,
        max_length=4,
    )

    @model_validator(mode="after")
    def validate_recommendations(self):
        time_slot_codes = [
            recommendation.timeSlot
            for recommendation in self.recommendations
        ]

        if len(time_slot_codes) != len(set(time_slot_codes)):
            raise ValueError("응답에 중복된 시간대가 있습니다.")

        ordered_codes = sorted(
            time_slot_codes,
            key=lambda code: TIME_SLOT_ORDER[code],
        )

        if time_slot_codes != ordered_codes:
            raise ValueError(
                "응답 시간대는 아침, 낮, 오후, 저녁 순서여야 합니다."
            )

        return self
