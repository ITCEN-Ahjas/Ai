from fastapi import APIRouter

from app.schemas.recommend import (
    RouteRecommendationRequest,
    RouteRecommendationResponse,
)
from app.services.recommend_service import recommend_service

router = APIRouter()


@router.post(
    "/routes",
    response_model=RouteRecommendationResponse,
    summary="Weather based AI travel route recommendation",
    description=(
        "Recommend a Chungbuk travel route using user preferences, "
        "time constraints, hourly weather, and verified candidate places."
    ),
)
def recommend_route(
    body: RouteRecommendationRequest,
) -> RouteRecommendationResponse:
    return recommend_service.recommend_route(body)
