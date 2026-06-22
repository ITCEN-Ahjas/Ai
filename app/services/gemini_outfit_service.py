from pydantic import ValidationError

from app.config import settings
from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import (GeminiOutfitCopy,
                                         OutfitRecommendationResponse)


class GeminiOutfitGenerationError(Exception):
    pass


class GeminiOutfitService:
    def generate(
        self,
        request: OutfitRecommendationRequest,
        fallback: OutfitRecommendationResponse,
    ) -> GeminiOutfitCopy:
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
            client = genai.Client(
                api_key=settings.gemini_api_key,
            )

            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=self._build_prompt(
                    request=request,
                    fallback=fallback,
                ),
                config=self._create_generation_config(types),
            )

            if not response.text:
                raise GeminiOutfitGenerationError(
                    "Gemini 응답 본문이 비어 있습니다."
                )

            return GeminiOutfitCopy.model_validate_json(
                response.text
            )

        except GeminiOutfitGenerationError:
            raise

        except ValidationError as exception:
            raise GeminiOutfitGenerationError(
                "Gemini 응답 형식 검증에 실패했습니다."
            ) from exception

        except Exception as exception:
            raise GeminiOutfitGenerationError(
                "Gemini 추천 문구 생성 중 오류가 발생했습니다."
            ) from exception

    def _create_generation_config(self, types):
        config_fields = types.GenerateContentConfig.model_fields

        if "response_format" in config_fields:
            return types.GenerateContentConfig(
                response_format={
                    "text": {
                        "mime_type": "application/json",
                        "schema": GeminiOutfitCopy.model_json_schema(),
                    }
                }
            )

        if (
            "response_mime_type" in config_fields
            and "response_json_schema" in config_fields
        ):
            return types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=GeminiOutfitCopy.model_json_schema(),
            )

        if (
            "response_mime_type" in config_fields
            and "response_schema" in config_fields
        ):
            return types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiOutfitCopy,
            )

        raise GeminiOutfitGenerationError(
            "현재 google-genai SDK에서 지원하는 구조화 응답 설정을 찾지 못했습니다."
        )

    def _build_prompt(
        self,
        request: OutfitRecommendationRequest,
        fallback: OutfitRecommendationResponse,
    ) -> str:
        current_weather = request.currentWeather
        feels_like_weather = request.feelsLikeWeather
        outfit_cards = fallback.outfitCards

        preparation_text = "\n".join(
            [
                (
                    f"- code: {item.code}, "
                    f"이름: {item.name}, "
                    f"기본 설명: {item.description}"
                )
                for item in fallback.preparationItems
            ]
        )

        return f"""
당신은 충청북도를 여행하는 외국인 방문자를 위한 옷차림 안내 문구 작성 도우미입니다.

아래에 이미 확정된 옷차림 카드 이름과 준비물 이름이 있습니다.
당신은 이름을 변경하거나 새 항목을 추천하면 안 됩니다.
각 카드와 준비물에 표시할 짧고 자연스러운 한국어 설명만 작성하세요.

반드시 지켜야 할 규칙:
1. 의류 이름, 준비물 이름, 준비물 code를 변경하지 마세요.
2. 브랜드명, 쇼핑 링크, 가격, 성별 표현을 사용하지 마세요.
3. 설명은 카드당 1문장으로 작성하세요.
4. 설명은 45자 이내의 쉬운 한국어로 작성하세요.
5. 제공된 준비물 code만 사용하세요.
6. 결과는 JSON 스키마에 맞춰 반환하세요.

[여행 정보]
- 지역: {request.region}
- 여행 스타일: {request.travelStyle}

[날씨 정보]
- 현재 기온: {current_weather.temperature}°C
- 체감온도: {feels_like_weather.feelsLikeTemperature}°C
- 습도: {current_weather.humidity}%
- 풍속: {current_weather.windSpeed}m/s
- 바람 상태: {current_weather.windStatus}
- 강수 형태: {current_weather.precipitationType}
- 강수 확률: {current_weather.precipitationProbability}%
- 하늘 상태: {current_weather.skyStatus}

[확정된 옷차림 카드]
- 아우터: {outfit_cards.outerwear.name}
- 상의: {outfit_cards.top.name}
- 하의: {outfit_cards.bottom.name}
- 신발: {outfit_cards.shoes.name}

[확정된 준비물]
{preparation_text}
""".strip()