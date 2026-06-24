from types import SimpleNamespace

from app.schemas.outfit_response import OutfitSelection
from app.schemas.outfit_time_slot_request import (
    TimeSlotOutfitRecommendationRequest,
)
from app.services.gemini_outfit_service import GeminiOutfitService


def create_selection_data() -> dict:
    return {
        "outerwearCode": "light_jacket",
        "topCode": "long_sleeve_tshirt",
        "bottomCode": "jeans",
        "shoesCode": "sneakers",
        "preparationCodes": ["light_outerwear", "water_bottle"],
    }


def create_time_slot_request() -> TimeSlotOutfitRecommendationRequest:
    return TimeSlotOutfitRecommendationRequest(
        region="청주",
        residenceWeather={
            "city": "New York",
            "country": "United States",
            "feelsLikeTemperature": -5.0,
        },
        timeSlots=[
            {
                "timeSlot": "afternoon",
                "timeSlotName": "오후",
                "forecastAt": "2026-06-24T15:00:00",
                "startTime": "14:00",
                "endTime": "17:00",
                "currentWeather": {
                    "temperature": 23.0,
                    "humidity": 55,
                    "windSpeed": 2.0,
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
        ],
    )


def test_parses_google_genai_parsed_response_first() -> None:
    service = GeminiOutfitService()

    response = SimpleNamespace(
        parsed=create_selection_data(),
        text="",
    )

    selection = service._parse_structured_response(
        response_model=OutfitSelection,
        response=response,
    )

    assert selection.outerwearCode == "light_jacket"
    assert selection.preparationCodes == [
        "light_outerwear",
        "water_bottle",
    ]


def test_parses_json_response_wrapped_in_code_fence() -> None:
    service = GeminiOutfitService()

    response = SimpleNamespace(
        parsed=None,
        text="""```json
{
  \"outerwearCode\": \"light_jacket\",
  \"topCode\": \"long_sleeve_tshirt\",
  \"bottomCode\": \"jeans\",
  \"shoesCode\": \"sneakers\",
  \"preparationCodes\": [\"light_outerwear\", \"water_bottle\"]
}
```""",
    )

    selection = service._parse_structured_response(
        response_model=OutfitSelection,
        response=response,
    )

    assert selection.shoesCode == "sneakers"


def test_time_slot_prompt_includes_residence_weather_context() -> None:
    service = GeminiOutfitService()
    request = create_time_slot_request()

    prompt = service._build_time_slot_prompt(
        request=request,
        fallback_selections={
            "afternoon": OutfitSelection(**create_selection_data()),
        },
    )

    assert "도시: New York, United States" in prompt
    assert "현재 거주 도시 체감온도: -5.0°C" in prompt
    assert "충북이 현재 거주 도시보다 약 28.0°C 더 따뜻함" in prompt
    assert "보조 기준" in prompt
