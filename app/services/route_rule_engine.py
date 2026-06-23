from __future__ import annotations

from datetime import datetime, time, timedelta

from app.schemas.recommend import (
    CandidatePlace,
    HourlyWeather,
    PlanBOption,
    RoutePlace,
    RouteRecommendationRequest,
    RouteRecommendationResponse,
    WeatherNote,
)


class RouteRuleEngine:
    PACE_LIMITS = {
        "relaxed": 3,
        "balanced": 4,
        "tight": 5,
    }

    def recommend(
        self,
        request: RouteRecommendationRequest,
    ) -> RouteRecommendationResponse:
        selected_places = self._select_places(request)
        itinerary = self._build_itinerary(
            request=request,
            places=selected_places,
        )
        weather_notes = self._build_weather_notes(request.weatherTimeline)
        plan_b = self._build_plan_b(
            itinerary=itinerary,
            candidates=request.candidatePlaces,
            weather_timeline=request.weatherTimeline,
        )

        return RouteRecommendationResponse(
            region=request.region,
            source="fallback",
            summary=self._build_summary(
                request=request,
                itinerary=itinerary,
            ),
            itinerary=itinerary,
            planB=plan_b,
            weatherNotes=weather_notes,
        )

    def _select_places(
        self,
        request: RouteRecommendationRequest,
    ) -> list[CandidatePlace]:
        limit = self.PACE_LIMITS[request.preference.activityPace]

        scored_places = [
            (self._score_place(request, place), index, place)
            for index, place in enumerate(request.candidatePlaces)
        ]
        scored_places.sort(key=lambda item: (-item[0], item[1]))

        return [place for _, _, place in scored_places[:limit]]

    def _score_place(
        self,
        request: RouteRecommendationRequest,
        place: CandidatePlace,
    ) -> int:
        score = 0
        matched_interests = set(request.preference.interests) & set(
            place.interests
        )

        score += len(matched_interests) * 30

        if place.indoor and self._has_bad_weather(request.weatherTimeline):
            score += 16

        if not place.indoor and self._has_good_outdoor_weather(
            request.weatherTimeline
        ):
            score += 10

        if request.preference.companionType == "family" and place.indoor:
            score += 5

        if (
            request.preference.transportMode == "walk"
            and place.averageStayMinutes <= 120
        ):
            score += 4

        return score

    def _build_itinerary(
        self,
        request: RouteRecommendationRequest,
        places: list[CandidatePlace],
    ) -> list[RoutePlace]:
        current_time = request.constraint.startTime
        end_time = request.constraint.endTime
        remaining_places = places.copy()
        itinerary: list[RoutePlace] = []

        while remaining_places and current_time < end_time:
            weather = self._find_weather_for_time(
                request.weatherTimeline,
                current_time,
            )
            preferred_indoor = self._should_prefer_indoor(weather)
            place = self._pop_best_time_slot_place(
                places=remaining_places,
                preferred_indoor=preferred_indoor,
                current_time=current_time,
            )
            visit_minutes = self._get_visit_minutes(
                request=request,
                place=place,
            )
            item_end_time = self._add_minutes(current_time, visit_minutes)

            if item_end_time > end_time:
                break

            itinerary.append(
                RoutePlace(
                    placeId=place.placeId,
                    name=place.name,
                    category=place.category,
                    startTime=current_time,
                    endTime=item_end_time,
                    indoor=place.indoor,
                    recommendationReason=self._build_recommendation_reason(
                        request=request,
                        place=place,
                    ),
                    weatherReason=self._build_weather_reason(
                        weather=weather,
                        place=place,
                    ),
                    moveTip=self._build_move_tip(request),
                )
            )
            current_time = self._add_minutes(item_end_time, 30)

        if itinerary:
            return itinerary

        fallback_place = places[0]
        fallback_end_time = min(
            self._add_minutes(current_time, 60),
            end_time,
        )

        return [
            RoutePlace(
                placeId=fallback_place.placeId,
                name=fallback_place.name,
                category=fallback_place.category,
                startTime=current_time,
                endTime=fallback_end_time,
                indoor=fallback_place.indoor,
                recommendationReason=self._build_recommendation_reason(
                    request=request,
                    place=fallback_place,
                ),
                weatherReason="The schedule is shortened to fit the available travel time.",
                moveTip=self._build_move_tip(request),
            )
        ]

    def _pop_best_time_slot_place(
        self,
        places: list[CandidatePlace],
        preferred_indoor: bool,
        current_time: time,
    ) -> CandidatePlace:
        for index, place in enumerate(places):
            if (
                place.indoor == preferred_indoor
                and self._is_open_at(place, current_time)
            ):
                return places.pop(index)

        for index, place in enumerate(places):
            if self._is_open_at(place, current_time):
                return places.pop(index)

        return places.pop(0)

    def _get_visit_minutes(
        self,
        request: RouteRecommendationRequest,
        place: CandidatePlace,
    ) -> int:
        if request.preference.activityPace == "relaxed":
            return min(place.averageStayMinutes + 15, 180)

        if request.preference.activityPace == "tight":
            return max(place.averageStayMinutes - 20, 45)

        return place.averageStayMinutes

    def _build_recommendation_reason(
        self,
        request: RouteRecommendationRequest,
        place: CandidatePlace,
    ) -> str:
        matched_interests = [
            interest
            for interest in request.preference.interests
            if interest in place.interests
        ]

        if matched_interests:
            return (
                f"{place.name} matches the user's "
                f"{', '.join(matched_interests)} preference."
            )

        return (
            f"{place.name} is included as a balanced stop for this route."
        )

    def _build_weather_reason(
        self,
        weather: HourlyWeather | None,
        place: CandidatePlace,
    ) -> str:
        if weather is None:
            return "No exact hourly weather matched this slot, so the route uses the nearest available plan."

        if self._should_prefer_indoor(weather) and place.indoor:
            return (
                "This indoor stop is placed during rain, heat, cold, or poor air quality."
            )

        if self._is_good_for_outdoor(weather) and not place.indoor:
            return "This outdoor stop is placed during a comfortable weather slot."

        if not place.indoor:
            return "This outdoor stop is kept in the route, but weather changes should be checked."

        return "This stop keeps the route flexible for changing weather."

    def _build_move_tip(
        self,
        request: RouteRecommendationRequest,
    ) -> str:
        transport_mode = request.preference.transportMode

        if transport_mode == "walk":
            return "Keep walking time short between stops."

        if transport_mode == "car":
            return "Check parking and road conditions before moving."

        if transport_mode == "taxi":
            return "Use taxi movement for long gaps between stops."

        return "Check local bus or taxi options before departure."

    def _build_weather_notes(
        self,
        weather_timeline: list[HourlyWeather],
    ) -> list[WeatherNote]:
        notes: list[WeatherNote] = []

        for weather in weather_timeline:
            if self._is_uncertain_rain(weather):
                notes.append(
                    WeatherNote(
                        timeRange=self._format_hour_range(weather.time),
                        summary=(
                            "Rain probability is uncertain, so a flexible indoor alternative is recommended."
                        ),
                        cautionLevel="medium",
                    )
                )
                continue

            if self._should_prefer_indoor(weather):
                notes.append(
                    WeatherNote(
                        timeRange=self._format_hour_range(weather.time),
                        summary=(
                            "Indoor stops are recommended for this time because weather conditions may reduce comfort."
                        ),
                        cautionLevel="high",
                    )
                )

        return notes[:5]

    def _build_plan_b(
        self,
        itinerary: list[RoutePlace],
        candidates: list[CandidatePlace],
        weather_timeline: list[HourlyWeather],
    ) -> list[PlanBOption]:
        if not any(self._is_uncertain_rain(weather) for weather in weather_timeline):
            return []

        outdoor_stop = next(
            (item for item in itinerary if not item.indoor),
            None,
        )
        indoor_candidate = next(
            (
                place
                for place in candidates
                if place.indoor
                and (
                    outdoor_stop is None
                    or place.placeId != outdoor_stop.placeId
                )
            ),
            None,
        )

        if outdoor_stop is None or indoor_candidate is None:
            return []

        return [
            PlanBOption(
                triggerCondition="If rain starts or the forecast worsens",
                replaceFrom=outdoor_stop.name,
                replaceTo=indoor_candidate.name,
                reason=(
                    "The alternative keeps the route comfortable without relying on outdoor conditions."
                ),
            )
        ]

    def _build_summary(
        self,
        request: RouteRecommendationRequest,
        itinerary: list[RoutePlace],
    ) -> str:
        indoor_count = len([item for item in itinerary if item.indoor])
        outdoor_count = len(itinerary) - indoor_count

        return (
            f"{request.region} route with {len(itinerary)} stops, "
            f"balancing {outdoor_count} outdoor and {indoor_count} indoor stops "
            "based on preferences and hourly weather."
        )

    def _find_weather_for_time(
        self,
        weather_timeline: list[HourlyWeather],
        target_time: time,
    ) -> HourlyWeather | None:
        target_minutes = self._to_minutes(target_time)

        return min(
            weather_timeline,
            key=lambda weather: abs(self._to_minutes(weather.time) - target_minutes),
            default=None,
        )

    def _has_bad_weather(
        self,
        weather_timeline: list[HourlyWeather],
    ) -> bool:
        return any(
            self._should_prefer_indoor(weather)
            for weather in weather_timeline
        )

    def _has_good_outdoor_weather(
        self,
        weather_timeline: list[HourlyWeather],
    ) -> bool:
        return any(
            self._is_good_for_outdoor(weather)
            for weather in weather_timeline
        )

    def _should_prefer_indoor(self, weather: HourlyWeather | None) -> bool:
        if weather is None:
            return False

        return (
            weather.condition in {"rain", "snow", "heat", "cold", "dust"}
            or weather.precipitationProbability >= 60
            or weather.feelsLikeTemperature >= 30
            or weather.feelsLikeTemperature <= 0
            or weather.fineDustLevel in {"bad", "very_bad"}
        )

    def _is_good_for_outdoor(self, weather: HourlyWeather) -> bool:
        return (
            weather.condition in {"clear", "cloudy"}
            and weather.precipitationProbability < 40
            and 5 < weather.feelsLikeTemperature < 30
            and weather.fineDustLevel in {"good", "normal"}
        )

    def _is_uncertain_rain(self, weather: HourlyWeather) -> bool:
        return 40 <= weather.precipitationProbability <= 60

    def _is_open_at(
        self,
        place: CandidatePlace,
        target_time: time,
    ) -> bool:
        if place.openTime is None or place.closeTime is None:
            return True

        return place.openTime <= target_time < place.closeTime

    def _format_hour_range(self, start_time: time) -> str:
        end_time = self._add_minutes(start_time, 60)

        return f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"

    def _add_minutes(self, value: time, minutes: int) -> time:
        base = datetime.combine(datetime.today(), value)

        return (base + timedelta(minutes=minutes)).time().replace(second=0)

    def _to_minutes(self, value: time) -> int:
        return value.hour * 60 + value.minute
