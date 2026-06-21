from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import OutfitRecommendationResponse
from app.services.outfit_rule_engine import OutfitRuleEngine


class OutfitRecommendationService:
    def __init__(self) -> None:
        self.rule_engine = OutfitRuleEngine()

    def recommend(
        self,
        request: OutfitRecommendationRequest,
    ) -> OutfitRecommendationResponse:
        return self.rule_engine.recommend(request)


outfit_recommendation_service = OutfitRecommendationService()