from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import (OutfitCard, OutfitCards,
                                         OutfitRecommendationResponse)
from app.services.gemini_outfit_service import (GeminiOutfitGenerationError,
                                                GeminiOutfitService)
from app.services.outfit_rule_engine import OutfitRuleEngine


class OutfitRecommendationService:
    def __init__(
        self,
        rule_engine: OutfitRuleEngine | None = None,
        gemini_outfit_service: GeminiOutfitService | None = None,
    ) -> None:
        self.rule_engine = rule_engine or OutfitRuleEngine()
        self.gemini_outfit_service = (
            gemini_outfit_service or GeminiOutfitService()
        )

    def recommend(
        self,
        request: OutfitRecommendationRequest,
    ) -> OutfitRecommendationResponse:
        fallback_response = self.rule_engine.recommend(request)

        try:
            gemini_copy = self.gemini_outfit_service.generate(
                request=request,
                fallback=fallback_response,
            )

            return self._apply_gemini_copy(
                fallback=fallback_response,
                gemini_copy=gemini_copy,
            )

        except GeminiOutfitGenerationError:
            return fallback_response

    def _apply_gemini_copy(
        self,
        fallback: OutfitRecommendationResponse,
        gemini_copy,
    ) -> OutfitRecommendationResponse:
        outfit_cards = OutfitCards(
            outerwear=OutfitCard(
                name=fallback.outfitCards.outerwear.name,
                description=gemini_copy.outerwearDescription,
            ),
            top=OutfitCard(
                name=fallback.outfitCards.top.name,
                description=gemini_copy.topDescription,
            ),
            bottom=OutfitCard(
                name=fallback.outfitCards.bottom.name,
                description=gemini_copy.bottomDescription,
            ),
            shoes=OutfitCard(
                name=fallback.outfitCards.shoes.name,
                description=gemini_copy.shoesDescription,
            ),
        )

        generated_descriptions = {
            item.code: item.description
            for item in gemini_copy.preparationDescriptions
        }

        preparation_items = [
            item.model_copy(
                update={
                    "description": generated_descriptions.get(
                        item.code,
                        item.description,
                    )
                }
            )
            for item in fallback.preparationItems
        ]

        return fallback.model_copy(
            update={
                "source": "ai",
                "outfitCards": outfit_cards,
                "preparationItems": preparation_items,
            }
        )


outfit_recommendation_service = OutfitRecommendationService()