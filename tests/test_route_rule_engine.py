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
) -> CandidatePlace:
    return CandidatePlace(
        placeId=place_id,
        name=name,
        category=category,
        interests=interests,
        indoor=indoor,
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
            ),
            create_place(
                "museum-1",
                "Cheongju Museum",
                "museum",
                ["exhibition"],
                indoor=True,
            ),
            create_place(
                "food-1",
                "Local Restaurant",
                "restaurant",
                ["food"],
                indoor=True,
            ),
            create_place(
                "cafe-1",
                "Rainy Day Cafe",
                "cafe",
                ["cafe"],
                indoor=True,
            ),
            create_place(
                "activity-1",
                "Outdoor Activity Park",
                "experience",
                ["activity"],
                indoor=False,
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
