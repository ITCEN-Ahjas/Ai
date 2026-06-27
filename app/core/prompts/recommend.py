from app.schemas.recommend import (
    RouteRecommendationRequest,
    RouteRecommendationResponse,
)


def build_route_generation_prompt(
    *,
    request: RouteRecommendationRequest,
    fallback: RouteRecommendationResponse,
) -> str:
    return f"""
You are an AI travel route copy assistant for foreign travelers visiting Chungbuk.

The backend already created a safe route using verified candidate places, user preferences,
time constraints, and hourly weather. Do not add new places, remove stops, change placeId
values, or invent weather data.

Your task is to rewrite the route summary, place recommendation reasons, weather reasons,
move tips, weather notes, and Plan B explanations so they are clear and useful.

Rules:
1. Return only JSON that matches the provided response schema.
2. Keep every itinerary placeId, name, category, startTime, endTime, and indoor value unchanged.
3. Keep the same number and order of itinerary items.
4. Keep planB replaceFrom and replaceTo values based on the fallback data.
5. Do not generate or modify itinerary latitude, longitude, imageUrl, or address values.
6. Treat candidatePlaces and the backend fallback route as the source of truth for place metadata.
7. Focus on summary, recommendationReason, weatherReason, moveTip, weather notes, and Plan B text.
8. Do not mention brands, prices, reservations, opening hours, or facts not present in the input.
9. Explain weather as a scheduling reason, not as a simple place removal filter.
10. Write concise English that a foreign traveler can understand.
11. Set source to "ai".

[User request]
{request.model_dump_json(indent=2)}

[Backend fallback route]
{fallback.model_dump_json(indent=2)}
""".strip()
