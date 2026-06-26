import pytest
from pydantic import ValidationError

from app.schemas.recommend import (
    CandidatePlace,
    HourlyWeather,
    RouteOverview,
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
                address="Cheongju, Chungbuk",
                imageUrl="https://example.com/sangdang.jpg",
                latitude=36.652,
                longitude=127.492,
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
    assert request.candidatePlaces[0].imageUrl == (
        "https://example.com/sangdang.jpg"
    )
    assert request.candidatePlaces[0].latitude == 36.652


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


def test_route_place_accepts_map_planner_fields() -> None:
    route_place = RoutePlace(
        day=2,
        order=3,
        placeId="place-1",
        name="Sangdang Sanseong",
        category="nature",
        startTime="13:00",
        endTime="14:30",
        indoor=False,
        address="Cheongju, Chungbuk",
        imageUrl="https://example.com/sangdang.jpg",
        latitude=36.652,
        longitude=127.492,
        recommendationReason="Matches the user's nature preference.",
        weatherReason="Placed during a comfortable outdoor weather slot.",
    )

    assert route_place.day == 2
    assert route_place.order == 3
    assert route_place.address == "Cheongju, Chungbuk"
    assert route_place.imageUrl == "https://example.com/sangdang.jpg"
    assert route_place.latitude == 36.652
    assert route_place.longitude == 127.492


def test_route_place_rejects_invalid_map_coordinates() -> None:
    with pytest.raises(ValidationError):
        RoutePlace(
            placeId="place-1",
            name="Invalid Coordinate",
            category="nature",
            startTime="13:00",
            endTime="14:30",
            indoor=False,
            latitude=91,
            longitude=127.492,
            recommendationReason="Matches the user's nature preference.",
            weatherReason="Placed during a comfortable outdoor weather slot.",
        )


def test_route_overview_accepts_planner_summary_fields() -> None:
    overview = RouteOverview(
        title="Cheongju weather-aware travel route",
        region="Cheongju",
        totalPlaces=3,
        totalStayMinutes=270,
        startLocation="Cheongju Station",
        endLocation="Cheongju Terminal",
        styleTags=["balanced", "public_transport", "nature"],
        weatherSummary="Hourly weather is comfortable for outdoor stops.",
    )

    assert overview.title == "Cheongju weather-aware travel route"
    assert overview.totalPlaces == 3
    assert overview.totalStayMinutes == 270
    assert overview.styleTags == ["balanced", "public_transport", "nature"]


def test_route_overview_rejects_blank_style_tag() -> None:
    with pytest.raises(ValidationError):
        RouteOverview(
            title="Cheongju weather-aware travel route",
            region="Cheongju",
            totalPlaces=3,
            totalStayMinutes=270,
            startLocation="Cheongju Station",
            styleTags=["balanced", " "],
            weatherSummary="Hourly weather is comfortable for outdoor stops.",
        )
