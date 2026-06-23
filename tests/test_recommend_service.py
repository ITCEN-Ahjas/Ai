from app.schemas.recommend import (
    CandidatePlace,
    HourlyWeather,
    RouteRecommendationRequest,
    RouteRecommendationResponse,
    TravelConstraint,
    UserPreference,
)
from app.services.gemini_route_service import GeminiRouteGenerationError
from app.services.recommend_service import RecommendService
from app.services.route_rule_engine import RouteRuleEngine


class FakeGeminiRouteSuccessService:
    def generate(
        self,
        request: RouteRecommendationRequest,
        fallback: RouteRecommendationResponse,
    ) -> RouteRecommendationResponse:
        itinerary = [
            item.model_copy(
                update={
                    "recommendationReason": (
                        f"{item.name} is a good fit for this travel style."
                    ),
                    "weatherReason": (
                        "This stop is placed at this time because of the hourly weather."
                    ),
                }
            )
            for item in fallback.itinerary
        ]

        return fallback.model_copy(
            update={
                "source": "ai",
                "summary": "AI refined this Chungbuk route with weather-aware explanations.",
                "itinerary": itinerary,
            }
        )


class FakeGeminiRouteFailureService:
    def generate(
        self,
        request: RouteRecommendationRequest,
        fallback: RouteRecommendationResponse,
    ) -> RouteRecommendationResponse:
        raise GeminiRouteGenerationError("Gemini failed")


def create_request() -> RouteRecommendationRequest:
    return RouteRecommendationRequest(
        region="Cheongju",
        preference=UserPreference(
            interests=["nature", "food"],
            companionType="couple",
            budgetLevel="medium",
            activityPace="balanced",
            transportMode="public_transport",
        ),
        constraint=TravelConstraint(
            travelDate="2026-06-24",
            startTime="09:00",
            endTime="18:00",
            startLocation="Cheongju Station",
            endLocation="Cheongju Station",
        ),
        weatherTimeline=[
            HourlyWeather(
                time="09:00",
                condition="clear",
                precipitationProbability=10,
                temperature=23,
                feelsLikeTemperature=24,
                fineDustLevel="normal",
            ),
            HourlyWeather(
                time="12:00",
                condition="rain",
                precipitationProbability=80,
                temperature=24,
                feelsLikeTemperature=25,
                fineDustLevel="normal",
            ),
        ],
        candidatePlaces=[
            CandidatePlace(
                placeId="nature-1",
                name="Sangdang Sanseong",
                category="nature",
                interests=["nature"],
                indoor=False,
                averageStayMinutes=90,
                openTime="09:00",
                closeTime="20:00",
            ),
            CandidatePlace(
                placeId="food-1",
                name="Local Restaurant",
                category="restaurant",
                interests=["food"],
                indoor=True,
                averageStayMinutes=80,
                openTime="09:00",
                closeTime="20:00",
            ),
        ],
    )


def test_recommend_route_returns_ai_response_when_gemini_succeeds() -> None:
    service = RecommendService(
        rule_engine=RouteRuleEngine(),
        gemini_route_service=FakeGeminiRouteSuccessService(),
    )

    response = service.recommend_route(create_request())

    assert response.source == "ai"
    assert response.summary.startswith("AI refined")
    assert response.itinerary
    assert "hourly weather" in response.itinerary[0].weatherReason


def test_recommend_route_returns_fallback_when_gemini_fails() -> None:
    service = RecommendService(
        rule_engine=RouteRuleEngine(),
        gemini_route_service=FakeGeminiRouteFailureService(),
    )

    response = service.recommend_route(create_request())

    assert response.source == "fallback"
    assert response.itinerary
    assert response.summary
