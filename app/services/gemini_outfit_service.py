from pydantic import ValidationError

from app.config import settings
from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import OutfitSelection
from app.services.outfit_catalog import OutfitCatalog


class GeminiOutfitGenerationError(Exception):
    pass


class GeminiOutfitService:
    def __init__(self, catalog: OutfitCatalog | None = None) -> None:
        self.catalog = catalog or OutfitCatalog()

    def generate(
        self,
        request: OutfitRecommendationRequest,
        fallback_selection: OutfitSelection,
    ) -> OutfitSelection:
        if not settings.gemini_api_key.strip():
            raise GeminiOutfitGenerationError(
                "GEMINI_API_KEY가 설정되지 않았습니다."
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError as exception:
            raise GeminiOutfitGenerationError(
                "google-genai 패키지가 설치되지 않았습니다."
            ) from exception

        try:
            client = genai.Client(api_key=settings.gemini_api_key)

            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=self._build_prompt(
                    request=request,
                    fallback_selection=fallback_selection,
                ),
                config=self._create_generation_config(types),
            )

            if not response.text:
                raise GeminiOutfitGenerationError(
                    "Gemini 응답 본문이 비어 있습니다."
                )

            return OutfitSelection.model_validate_json(response.text)

        except GeminiOutfitGenerationError:
            raise

        except ValidationError as exception:
            raise GeminiOutfitGenerationError(
                "Gemini 응답 형식 검증에 실패했습니다."
            ) from exception

        except Exception as exception:
            raise GeminiOutfitGenerationError(
                "Gemini 추천 코드 생성 중 오류가 발생했습니다."
            ) from exception

    def _create_generation_config(self, types):
        config_fields = types.GenerateContentConfig.model_fields

        if "response_format" in config_fields:
            return types.GenerateContentConfig(
                response_format={
                    "text": {
                        "mime_type": "application/json",
                        "schema": OutfitSelection.model_json_schema(),
                    }
                }
            )

        if (
            "response_mime_type" in config_fields
            and "response_json_schema" in config_fields
        ):
            return types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=OutfitSelection.model_json_schema(),
            )

        if (
            "response_mime_type" in config_fields
            and "response_schema" in config_fields
        ):
            return types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=OutfitSelection,
            )

        raise GeminiOutfitGenerationError(
            "현재 google-genai SDK에서 지원하는 구조화 응답 설정을 찾지 못했습니다."
        )

    def _build_prompt(
        self,
        request: OutfitRecommendationRequest,
        fallback_selection: OutfitSelection,
    ) -> str:
        current_weather = request.currentWeather
        feels_like_weather = request.feelsLikeWeather

        return f"""
당신은 충청북도를 여행하는 외국인 방문자를 위한 옷차림 코드 선택 도우미입니다.

당신은 문장을 만들거나 카드 설명을 작성하면 안 됩니다.
반드시 제공된 카탈로그 안에서 코드만 선택해 JSON으로 반환하세요.

반드시 지켜야 할 규칙:
1. outerwearCode, topCode, bottomCode, shoesCode는 각 카테고리의 제공 코드만 사용하세요.
2. preparationCodes는 제공 코드만 사용하고 1개 이상 4개 이하로 선택하세요.
3. 브랜드명, 가격, 성별, 쇼핑 정보, 설명 문장을 절대 반환하지 마세요.
4. 실제 비가 오는 날에는 rain_boots 또는 waterproof_hiking_shoes를 우선 고려하세요.
5. 비가 올 가능성만 높을 때에는 waterproof_sneakers를 우선 고려하세요.
6. 눈 또는 결빙 가능성이 있으면 anti_slip_winter_boots를 우선 고려하세요.
7. 기본 규칙 선택이 안전한 경우 불필요하게 변경하지 마세요.

[여행 정보]
- 지역: {request.region}
- 여행 스타일: {request.travelStyle}

[날씨 정보]
- 현재 기온: {current_weather.temperature}°C
- 체감온도: {feels_like_weather.feelsLikeTemperature}°C
- 습도: {current_weather.humidity}%
- 풍속: {current_weather.windSpeed}m/s
- 바람 상태: {current_weather.windStatus}
- 강수량 설명: {current_weather.precipitationAmount}
- 강수 형태: {current_weather.precipitationType}
- 강수 확률: {current_weather.precipitationProbability}%
- 하늘 상태: {current_weather.skyStatus}
- 종합 날씨: {current_weather.weatherCondition}

[기본 규칙 선택]
- outerwearCode: {fallback_selection.outerwearCode}
- topCode: {fallback_selection.topCode}
- bottomCode: {fallback_selection.bottomCode}
- shoesCode: {fallback_selection.shoesCode}
- preparationCodes: {", ".join(fallback_selection.preparationCodes)}

[선택 가능한 카탈로그]
{self.catalog.get_prompt_catalog()}
""".strip()