from fastapi import APIRouter, BackgroundTasks

from app.schemas.outfit_batch_request import OutfitBatchRecommendationRequest
from app.schemas.outfit_batch_response import OutfitBatchRecommendationResponse
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


@router.post(
    "/recommendations",
    response_model=OutfitBatchRecommendationResponse,
    summary="여행 스타일 6개 옷차림 일괄 추천",
)
def recommend_outfits(
    body: OutfitBatchRecommendationRequest,
    background_tasks: BackgroundTasks,
) -> OutfitBatchRecommendationResponse:
    response = outfit_recommendation_service.recommend_batch(body)

    if (
        response.source == "fallback"
        and outfit_recommendation_service.reserve_batch_warmup(body)
    ):
        background_tasks.add_task(
            outfit_recommendation_service.warm_batch_cache,
            body,
        )

    return response