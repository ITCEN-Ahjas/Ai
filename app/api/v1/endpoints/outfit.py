from fastapi import APIRouter

from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import OutfitRecommendationResponse
from app.services.outfit_recommendation_service import \
    outfit_recommendation_service

router = APIRouter()


@router.post(
    "/recommend",
    response_model=OutfitRecommendationResponse,
    summary="날씨 기반 옷차림 추천",
)
def recommend_outfit(
    body: OutfitRecommendationRequest,
) -> OutfitRecommendationResponse:
    return outfit_recommendation_service.recommend(body)