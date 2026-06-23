from pydantic import BaseModel, ValidationError

from app.config import settings
from app.core.prompts.recommend import build_route_generation_prompt
from app.schemas.recommend import (
    RouteRecommendationRequest,
    RouteRecommendationResponse,
)


class GeminiRouteGenerationError(Exception):
    pass


class GeminiRouteService:
    def generate(
        self,
        request: RouteRecommendationRequest,
        fallback: RouteRecommendationResponse,
    ) -> RouteRecommendationResponse:
        result = self._generate_structured(
            response_model=RouteRecommendationResponse,
            prompt=build_route_generation_prompt(
                request=request,
                fallback=fallback,
            ),
        )

        response = RouteRecommendationResponse.model_validate(
            result.model_dump()
        )

        self._validate_preserved_route(
            fallback=fallback,
            generated=response,
        )

        return response.model_copy(update={"source": "ai"})

    def _generate_structured(
        self,
        *,
        response_model: type[BaseModel],
        prompt: str,
    ) -> BaseModel:
        if not settings.gemini_api_key.strip():
            raise GeminiRouteGenerationError(
                "GEMINI_API_KEY is not configured."
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError as exception:
            raise GeminiRouteGenerationError(
                "google-genai package is not installed."
            ) from exception

        try:
            client = genai.Client(
                api_key=settings.gemini_api_key,
            )

            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=self._create_generation_config(
                    types=types,
                    response_model=response_model,
                ),
            )

            if not response.text:
                raise GeminiRouteGenerationError(
                    "Gemini returned an empty response."
                )

            return response_model.model_validate_json(response.text)

        except GeminiRouteGenerationError:
            raise

        except ValidationError as exception:
            raise GeminiRouteGenerationError(
                "Gemini route response validation failed."
            ) from exception

        except Exception as exception:
            raise GeminiRouteGenerationError(
                "Gemini route generation failed."
            ) from exception

    def _create_generation_config(
        self,
        *,
        types,
        response_model: type[BaseModel],
    ):
        config_fields = types.GenerateContentConfig.model_fields
        response_schema = response_model.model_json_schema()

        if "response_format" in config_fields:
            return types.GenerateContentConfig(
                response_format={
                    "text": {
                        "mime_type": "application/json",
                        "schema": response_schema,
                    }
                }
            )

        if (
            "response_mime_type" in config_fields
            and "response_json_schema" in config_fields
        ):
            return types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=response_schema,
            )

        if (
            "response_mime_type" in config_fields
            and "response_schema" in config_fields
        ):
            return types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_model,
            )

        raise GeminiRouteGenerationError(
            "The installed google-genai SDK does not support structured responses."
        )

    def _validate_preserved_route(
        self,
        *,
        fallback: RouteRecommendationResponse,
        generated: RouteRecommendationResponse,
    ) -> None:
        if len(fallback.itinerary) != len(generated.itinerary):
            raise GeminiRouteGenerationError(
                "Gemini changed the itinerary length."
            )

        for fallback_item, generated_item in zip(
            fallback.itinerary,
            generated.itinerary,
        ):
            preserved_fields = [
                "placeId",
                "name",
                "category",
                "startTime",
                "endTime",
                "indoor",
            ]

            for field_name in preserved_fields:
                if getattr(fallback_item, field_name) != getattr(
                    generated_item,
                    field_name,
                ):
                    raise GeminiRouteGenerationError(
                        "Gemini changed a fixed itinerary field."
                    )
