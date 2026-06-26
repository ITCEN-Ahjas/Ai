from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_payload() -> dict:
    return {
        "region": "Cheongju",
        "preference": {
            "interests": ["nature", "food"],
            "companionType": "couple",
            "budgetLevel": "medium",
            "activityPace": "balanced",
            "transportMode": "public_transport",
        },
        "constraint": {
            "travelDate": "2026-06-24",
            "startTime": "09:00",
            "endTime": "18:00",
            "startLocation": "Cheongju Station",
            "endLocation": "Cheongju Station",
        },
        "weatherTimeline": [
            {
                "time": "09:00",
                "condition": "clear",
                "precipitationProbability": 10,
                "temperature": 23,
                "feelsLikeTemperature": 24,
                "fineDustLevel": "normal",
            },
            {
                "time": "12:00",
                "condition": "rain",
                "precipitationProbability": 80,
                "temperature": 24,
                "feelsLikeTemperature": 25,
                "fineDustLevel": "normal",
            },
        ],
        "candidatePlaces": [
            {
                "placeId": "nature-1",
                "name": "Sangdang Sanseong",
                "category": "nature",
                "interests": ["nature"],
                "indoor": False,
                "averageStayMinutes": 90,
                "openTime": "09:00",
                "closeTime": "20:00",
            },
            {
                "placeId": "food-1",
                "name": "Local Restaurant",
                "category": "restaurant",
                "interests": ["food"],
                "indoor": True,
                "averageStayMinutes": 80,
                "openTime": "09:00",
                "closeTime": "20:00",
            },
        ],
    }


def test_recommend_route_endpoint_returns_route_response() -> None:
    response = client.post(
        "/api/v1/recommend/routes",
        json=create_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["region"] == "Cheongju"
    assert body["source"] in {"ai", "fallback"}
    assert body["summary"]
    assert len(body["itinerary"]) >= 1
    assert "planB" in body
    assert "weatherNotes" in body


def test_recommend_route_endpoint_rejects_invalid_payload() -> None:
    payload = create_payload()
    payload["constraint"]["startTime"] = "18:00"
    payload["constraint"]["endTime"] = "09:00"

    response = client.post(
        "/api/v1/recommend/routes",
        json=payload,
    )

    assert response.status_code == 422


def test_recommend_options_endpoint_returns_schema_options() -> None:
    response = client.get("/api/v1/recommend/options")

    assert response.status_code == 200

    body = response.json()

    assert "Cheongju" in body["regions"]
    assert body["interests"] == [
        "nature",
        "food",
        "exhibition",
        "activity",
        "shopping",
        "festival",
        "cafe",
    ]
    assert body["companionTypes"] == [
        "solo",
        "couple",
        "family",
        "friends",
    ]
    assert body["budgetLevels"] == ["low", "medium", "high"]
    assert body["activityPaces"] == ["relaxed", "balanced", "tight"]
    assert body["transportModes"] == [
        "walk",
        "public_transport",
        "car",
        "taxi",
    ]
    assert "restaurant" in body["placeCategories"]
    assert "rain" in body["weatherConditions"]
    assert body["fineDustLevels"] == [
        "good",
        "normal",
        "bad",
        "very_bad",
    ]
