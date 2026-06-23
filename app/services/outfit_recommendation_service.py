from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import OutfitRecommendationResponse
from app.services.gemini_outfit_service import (GeminiOutfitGenerationError,
                                                GeminiOutfitService)
from app.services.outfit_catalog import (InvalidOutfitSelectionError,
                                         OutfitCatalog)
from app.services.outfit_rule_engine import OutfitRuleEngine


class OutfitRecommendationService:
    def __init__(
        self,
        rule_engine: OutfitRuleEngine | None = None,
        catalog: OutfitCatalog | None = None,
        gemini_outfit_service: GeminiOutfitService | None = None,
    ) -> None:
        self.rule_engine = rule_engine or OutfitRuleEngine()
        self.catalog = catalog or OutfitCatalog()
        self.gemini_outfit_service = (
            gemini_outfit_service or GeminiOutfitService(self.catalog)
        )

    def recommend(
        self,
        request: OutfitRecommendationRequest,
    ) -> OutfitRecommendationResponse:
        fallback_selection = self.rule_engine.select(request)

        try:
            gemini_selection = self.gemini_outfit_service.generate(
                request=request,
                fallback_selection=fallback_selection,
            )

            return self.catalog.build_response(
                region=request.region,
                travel_style=request.travelStyle,
                selection=gemini_selection,
                source="ai",
            )

        except (
            GeminiOutfitGenerationError,
            InvalidOutfitSelectionError,
        ):
            return self.catalog.build_response(
                region=request.region,
                travel_style=request.travelStyle,
                selection=fallback_selection,
                source="fallback",
            )


outfit_recommendation_service = OutfitRecommendationService()