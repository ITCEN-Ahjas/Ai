import pytest
from pydantic import ValidationError

from app.schemas.recommend import (
    CandidatePlace,
    HourlyWeather,
    RouteRecommendationRequest,
    RoutePlace,
    TravelConstraint,
    UserPreference,
)


def create_request() -> RouteRecommendationRequest:
    return RouteRecommendationRequest(
        region="Cheongju",
        preference=UserPreference(
            interests=["nature", "food", "nature"],
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
                temperature=24,
                feelsLikeTemperature=25,
                fineDustLevel="normal",
            )
        ],
        candidatePlaces=[
            CandidatePlace(
                placeId="place-1",
                name="Sangdang Sanseong",
                category="nature",
                interests=["nature"],
                indoor=False,
                averageStayMinutes=90,
                openTime="09:00",
                closeTime="18:00",
            )
        ],
    )


def test_route_recommendation_request_accepts_form_based_inputs() -> None:
    request = create_request()

    assert request.region == "Cheongju"
    assert request.preference.interests == ["nature", "food"]
    assert request.constraint.startLocation == "Cheongju Station"
    assert len(request.weatherTimeline) == 1
    assert len(request.candidatePlaces) == 1


def test_route_recommendation_request_rejects_invalid_time_range() -> None:
    with pytest.raises(ValidationError):
        TravelConstraint(
            travelDate="2026-06-24",
            startTime="18:00",
            endTime="09:00",
            startLocation="Cheongju Station",
        )


def test_route_recommendation_request_rejects_invalid_weather_probability() -> None:
    with pytest.raises(ValidationError):
        HourlyWeather(
            time="15:00",
            condition="rain",
            precipitationProbability=101,
            temperature=25,
            feelsLikeTemperature=26,
        )


def test_candidate_place_rejects_invalid_opening_hours() -> None:
    with pytest.raises(ValidationError):
        CandidatePlace(
            placeId="place-1",
            name="Invalid Place",
            category="cafe",
            interests=["cafe"],
            indoor=True,
            openTime="18:00",
            closeTime="09:00",
        )


def test_route_place_requires_valid_schedule_order() -> None:
    with pytest.raises(ValidationError):
        RoutePlace(
            placeId="place-1",
            name="Invalid Schedule",
            category="cafe",
            startTime="13:00",
            endTime="12:00",
            indoor=True,
            recommendationReason="Matches the user's cafe preference.",
            weatherReason="Useful during the rainy time slot.",
        )
