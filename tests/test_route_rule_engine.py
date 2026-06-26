from app.schemas.recommend import (
    CandidatePlace,
    HourlyWeather,
    RouteRecommendationRequest,
    TravelConstraint,
    UserPreference,
)
from app.services.route_rule_engine import RouteRuleEngine


def create_place(
    place_id: str,
    name: str,
    category: str,
    interests: list[str],
    indoor: bool,
    average_stay_minutes: int = 90,
    address: str | None = None,
    image_url: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> CandidatePlace:
    return CandidatePlace(
        placeId=place_id,
        name=name,
        category=category,
        interests=interests,
        indoor=indoor,
        address=address,
        imageUrl=image_url,
        latitude=latitude,
        longitude=longitude,
        averageStayMinutes=average_stay_minutes,
        openTime="09:00",
        closeTime="20:00",
    )


def create_weather(
    time: str,
    condition: str,
    precipitation_probability: int,
    feels_like_temperature: float,
    fine_dust_level: str = "normal",
) -> HourlyWeather:
    return HourlyWeather(
        time=time,
        condition=condition,
        precipitationProbability=precipitation_probability,
        temperature=feels_like_temperature,
        feelsLikeTemperature=feels_like_temperature,
        fineDustLevel=fine_dust_level,
    )


def create_request(
    *,
    activity_pace: str = "balanced",
    interests: list[str] | None = None,
    weather_timeline: list[HourlyWeather] | None = None,
) -> RouteRecommendationRequest:
    return RouteRecommendationRequest(
        region="Cheongju",
        preference=UserPreference(
            interests=interests or ["nature", "food"],
            companionType="couple",
            budgetLevel="medium",
            activityPace=activity_pace,
            transportMode="public_transport",
        ),
        constraint=TravelConstraint(
            travelDate="2026-06-24",
            startTime="09:00",
            endTime="18:00",
            startLocation="Cheongju Station",
            endLocation="Cheongju Station",
        ),
        weatherTimeline=weather_timeline
        or [
            create_weather("09:00", "clear", 10, 22),
            create_weather("12:00", "clear", 20, 26),
            create_weather("15:00", "clear", 10, 24),
        ],
        candidatePlaces=[
            create_place(
                "nature-1",
                "Sangdang Sanseong",
                "nature",
                ["nature"],
                indoor=False,
                address="Cheongju Sangdang-gu",
                image_url="https://example.com/nature.jpg",
                latitude=36.652,
                longitude=127.492,
            ),
            create_place(
                "museum-1",
                "Cheongju Museum",
                "museum",
                ["exhibition"],
                indoor=True,
                address="Cheongju Museum Road",
                image_url="https://example.com/museum.jpg",
                latitude=36.641,
                longitude=127.488,
            ),
            create_place(
                "food-1",
                "Local Restaurant",
                "restaurant",
                ["food"],
                indoor=True,
                address="Cheongju Food Street",
                image_url="https://example.com/food.jpg",
                latitude=36.635,
                longitude=127.491,
            ),
            create_place(
                "cafe-1",
                "Rainy Day Cafe",
                "cafe",
                ["cafe"],
                indoor=True,
                address="Cheongju Cafe Street",
                image_url="https://example.com/cafe.jpg",
                latitude=36.633,
                longitude=127.489,
            ),
            create_place(
                "activity-1",
                "Outdoor Activity Park",
                "experience",
                ["activity"],
                indoor=False,
                address="Cheongju Activity Park",
                image_url="https://example.com/activity.jpg",
                latitude=36.629,
                longitude=127.486,
            ),
        ],
    )


def test_rainy_time_slot_prefers_indoor_place() -> None:
    response = RouteRuleEngine().recommend(
        create_request(
            weather_timeline=[
                create_weather("09:00", "rain", 80, 21),
                create_weather("12:00", "clear", 10, 24),
                create_weather("15:00", "clear", 10, 23),
            ]
        )
    )

    assert response.source == "fallback"
    assert response.itinerary[0].indoor is True
    assert "indoor" in response.itinerary[0].weatherReason.lower()


def test_clear_time_slot_can_place_outdoor_stop_first() -> None:
    response = RouteRuleEngine().recommend(create_request())

    assert response.itinerary[0].name == "Sangdang Sanseong"
    assert response.itinerary[0].indoor is False


def test_heat_time_slot_prefers_indoor_place() -> None:
    response = RouteRuleEngine().recommend(
        create_request(
            weather_timeline=[
                create_weather("09:00", "heat", 10, 33),
                create_weather("12:00", "heat", 20, 35),
                create_weather("15:00", "clear", 10, 27),
            ]
        )
    )

    assert response.itinerary[0].indoor is True
    assert response.weatherNotes[0].cautionLevel == "high"


def test_interest_matching_places_are_prioritized() -> None:
    response = RouteRuleEngine().recommend(
        create_request(
            interests=["exhibition"],
            weather_timeline=[
                create_weather("09:00", "rain", 80, 21),
                create_weather("12:00", "clear", 10, 24),
                create_weather("15:00", "clear", 10, 23),
            ],
        )
    )

    assert response.itinerary[0].name == "Cheongju Museum"
    assert "exhibition" in response.itinerary[0].recommendationReason


def test_activity_pace_changes_itinerary_size() -> None:
    relaxed_response = RouteRuleEngine().recommend(
        create_request(activity_pace="relaxed")
    )
    tight_response = RouteRuleEngine().recommend(
        create_request(activity_pace="tight")
    )

    assert len(relaxed_response.itinerary) == 3
    assert len(tight_response.itinerary) == 5


def test_uncertain_rain_adds_weather_note_and_plan_b() -> None:
    response = RouteRuleEngine().recommend(
        create_request(
            weather_timeline=[
                create_weather("09:00", "clear", 50, 22),
                create_weather("12:00", "clear", 20, 25),
                create_weather("15:00", "clear", 10, 24),
            ]
        )
    )

    assert any(note.cautionLevel == "medium" for note in response.weatherNotes)
    assert len(response.planB) == 1
    assert response.planB[0].replaceFrom
    assert response.planB[0].replaceTo


def test_itinerary_preserves_candidate_place_map_metadata() -> None:
    response = RouteRuleEngine().recommend(create_request())
    first_place = response.itinerary[0]

    assert first_place.day == 1
    assert first_place.order == 1
    assert first_place.address == "Cheongju Sangdang-gu"
    assert first_place.imageUrl == "https://example.com/nature.jpg"
    assert first_place.latitude == 36.652
    assert first_place.longitude == 127.492


def test_itinerary_assigns_sequential_order_values() -> None:
    response = RouteRuleEngine().recommend(
        create_request(activity_pace="tight")
    )

    assert [item.order for item in response.itinerary] == [1, 2, 3, 4, 5]
    assert all(item.day == 1 for item in response.itinerary)


def test_route_overview_is_created_for_planner_summary() -> None:
    response = RouteRuleEngine().recommend(create_request())

    assert response.routeOverview.title == (
        "Cheongju weather-aware travel route"
    )
    assert response.routeOverview.region == "Cheongju"
    assert response.routeOverview.totalPlaces == len(response.itinerary)
    assert response.routeOverview.totalStayMinutes == 360
    assert response.routeOverview.startLocation == "Cheongju Station"
    assert response.routeOverview.endLocation == "Cheongju Station"
    assert "balanced" in response.routeOverview.styleTags
    assert "public_transport" in response.routeOverview.styleTags
    assert response.routeOverview.weatherSummary


def test_route_overview_summarizes_weather_risk() -> None:
    response = RouteRuleEngine().recommend(
        create_request(
            weather_timeline=[
                create_weather("09:00", "rain", 80, 21),
                create_weather("12:00", "clear", 10, 24),
                create_weather("15:00", "clear", 10, 23),
            ]
        )
    )

    assert "indoor stops" in response.routeOverview.weatherSummary
