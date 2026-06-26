from fastapi import APIRouter

from app.schemas.recommend import (
    RouteRecommendationRequest,
    RouteRecommendationResponse,
)
from app.services.recommend_service import recommend_service

router = APIRouter()

RECOMMENDATION_OPTIONS = {
    "regions": [
        "Cheongju",
        "Chungju",
        "Jecheon",
        "Boeun",
        "Okcheon",
        "Yeongdong",
        "Jeungpyeong",
        "Jincheon",
        "Goesan",
        "Eumseong",
        "Danyang",
    ],
    "interests": [
        "nature",
        "food",
        "exhibition",
        "activity",
        "shopping",
        "festival",
        "cafe",
    ],
    "companionTypes": [
        "solo",
        "couple",
        "family",
        "friends",
    ],
    "budgetLevels": [
        "low",
        "medium",
        "high",
    ],
    "activityPaces": [
        "relaxed",
        "balanced",
        "tight",
    ],
    "transportModes": [
        "walk",
        "public_transport",
        "car",
        "taxi",
    ],
    "placeCategories": [
        "nature",
        "restaurant",
        "cafe",
        "museum",
        "experience",
        "shopping",
        "festival",
        "landmark",
    ],
    "weatherConditions": [
        "clear",
        "cloudy",
        "rain",
        "snow",
        "heat",
        "cold",
        "dust",
    ],
    "fineDustLevels": [
        "good",
        "normal",
        "bad",
        "very_bad",
    ],
}


@router.get(
    "/options",
    summary="AI route recommendation input options",
    description=(
        "Return enum-like option values used by the AI route "
        "recommendation request schema."
    ),
)
def get_recommendation_options() -> dict[str, list[str]]:
    return RECOMMENDATION_OPTIONS


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
