from app.schemas.recommend import (
    RouteRecommendationRequest,
    RouteRecommendationResponse,
)
from app.services.gemini_route_service import (
    GeminiRouteGenerationError,
    GeminiRouteService,
)
from app.services.route_rule_engine import RouteRuleEngine


class RecommendService:
    def __init__(
        self,
        rule_engine: RouteRuleEngine | None = None,
        gemini_route_service: GeminiRouteService | None = None,
    ) -> None:
        self.rule_engine = rule_engine or RouteRuleEngine()
        self.gemini_route_service = gemini_route_service or GeminiRouteService()

    def recommend_route(
        self,
        request: RouteRecommendationRequest,
    ) -> RouteRecommendationResponse:
        fallback_response = self.rule_engine.recommend(request)

        try:
            return self.gemini_route_service.generate(
                request=request,
                fallback=fallback_response,
            )

        except GeminiRouteGenerationError:
            return fallback_response


recommend_service = RecommendService()
