from types import SimpleNamespace

from app.schemas.outfit_response import OutfitSelection
from app.services.gemini_outfit_service import GeminiOutfitService


def create_selection_data() -> dict:
    return {
        "outerwearCode": "light_jacket",
        "topCode": "long_sleeve_tshirt",
        "bottomCode": "jeans",
        "shoesCode": "sneakers",
        "preparationCodes": ["light_outerwear", "water_bottle"],
    }


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
