from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import OutfitSelection
from app.schemas.outfit_time_slot_request import (
    ResidenceWeatherRequest,
    TimeSlotWeatherRequest,
)
from app.services.outfit_catalog import OutfitCatalog
from app.services.outfit_rule_engine import OutfitRuleEngine


class TimeSlotOutfitRuleEngine:
    WARMER_RESIDENCE_GAP_THRESHOLD = 8.0
    COOLER_RESIDENCE_GAP_THRESHOLD = -8.0
    EXTREME_RESIDENCE_GAP_THRESHOLD = 15.0

    def __init__(self) -> None:
        self._base_rule_engine = OutfitRuleEngine()

    def select(
        self,
        *,
        region: str,
        time_slot_weather: TimeSlotWeatherRequest,
        residence_weather: ResidenceWeatherRequest | None = None,
    ) -> OutfitSelection:
        base_request = OutfitRecommendationRequest(
            region=region,
            travelStyle="기본 추천",
            currentWeather=time_slot_weather.currentWeather,
            feelsLikeWeather=time_slot_weather.feelsLikeWeather,
        )

        selection = self._base_rule_engine.select(base_request)
        selection = self._apply_time_slot_rule(
            time_slot_weather=time_slot_weather,
            selection=selection,
        )

        return self._apply_residence_climate_rule(
            time_slot_weather=time_slot_weather,
            residence_weather=residence_weather,
            selection=selection,
        )

    def _apply_time_slot_rule(
        self,
        *,
        time_slot_weather: TimeSlotWeatherRequest,
        selection: OutfitSelection,
    ) -> OutfitSelection:
        feels_like_temperature = (
            time_slot_weather.feelsLikeWeather.feelsLikeTemperature
        )

        if (
            time_slot_weather.timeSlot == "evening"
            and 17 <= feels_like_temperature < 24
            and not self._has_precipitation(time_slot_weather)
        ):
            return self._merge_selection(
                selection,
                outerwear_code="light_jacket",
                preparation_codes=["light_outerwear", "battery"],
            )

        if (
            time_slot_weather.timeSlot == "morning"
            and 17 <= feels_like_temperature < 22
            and not self._has_precipitation(time_slot_weather)
        ):
            return self._merge_selection(
                selection,
                outerwear_code="light_cardigan",
                preparation_codes=["light_outerwear"],
            )

        return selection

    def _apply_residence_climate_rule(
        self,
        *,
        time_slot_weather: TimeSlotWeatherRequest,
        residence_weather: ResidenceWeatherRequest | None,
        selection: OutfitSelection,
    ) -> OutfitSelection:
        if residence_weather is None:
            return selection

        if self._has_precipitation(time_slot_weather) or self._has_strong_wind(
            time_slot_weather
        ):
            return selection

        target_feels_like = (
            time_slot_weather.feelsLikeWeather.feelsLikeTemperature
        )
        temperature_gap = (
            target_feels_like - residence_weather.feelsLikeTemperature
        )

        if temperature_gap >= self.WARMER_RESIDENCE_GAP_THRESHOLD:
            return self._apply_warmer_than_residence_rule(
                time_slot_weather=time_slot_weather,
                selection=selection,
                temperature_gap=temperature_gap,
            )

        if temperature_gap <= self.COOLER_RESIDENCE_GAP_THRESHOLD:
            return self._apply_cooler_than_residence_rule(
                time_slot_weather=time_slot_weather,
                selection=selection,
                temperature_gap=temperature_gap,
            )

        return selection

    def _apply_warmer_than_residence_rule(
        self,
        *,
        time_slot_weather: TimeSlotWeatherRequest,
        selection: OutfitSelection,
        temperature_gap: float,
    ) -> OutfitSelection:
        target_feels_like = (
            time_slot_weather.feelsLikeWeather.feelsLikeTemperature
        )
        preparation_codes = ["water_bottle"]

        if time_slot_weather.timeSlot != "evening":
            preparation_codes.extend(["sunscreen", "hat"])

        if (
            temperature_gap >= self.EXTREME_RESIDENCE_GAP_THRESHOLD
            and target_feels_like >= 22
        ):
            return self._merge_selection(
                selection,
                outerwear_code="no_outer",
                top_code="short_sleeve_tshirt",
                bottom_code=(
                    "shorts"
                    if target_feels_like >= 26
                    else "lightweight_pants"
                ),
                shoes_code="breathable_sneakers",
                preparation_codes=preparation_codes,
            )

        if target_feels_like >= 22:
            return self._merge_selection(
                selection,
                outerwear_code="light_shirt",
                top_code="short_sleeve_tshirt",
                bottom_code="lightweight_pants",
                shoes_code="breathable_sneakers",
                preparation_codes=preparation_codes,
            )

        if target_feels_like >= 17:
            return self._merge_selection(
                selection,
                outerwear_code="light_shirt",
                top_code="light_long_sleeve",
                bottom_code="cotton_pants",
                preparation_codes=preparation_codes,
            )

        return selection

    def _apply_cooler_than_residence_rule(
        self,
        *,
        time_slot_weather: TimeSlotWeatherRequest,
        selection: OutfitSelection,
        temperature_gap: float,
    ) -> OutfitSelection:
        target_feels_like = (
            time_slot_weather.feelsLikeWeather.feelsLikeTemperature
        )
        preparation_codes = ["light_outerwear"]

        if target_feels_like < 12:
            preparation_codes.append("thermal_bottle")

        if (
            temperature_gap <= -self.EXTREME_RESIDENCE_GAP_THRESHOLD
            and target_feels_like < 17
        ):
            return self._merge_selection(
                selection,
                outerwear_code="heavy_jacket",
                top_code="knit",
                bottom_code="brushed_pants",
                shoes_code="insulated_sneakers",
                preparation_codes=preparation_codes,
            )

        if target_feels_like <= 22:
            return self._merge_selection(
                selection,
                outerwear_code="light_jacket",
                top_code="long_sleeve_tshirt",
                bottom_code="jeans",
                shoes_code="sneakers",
                preparation_codes=preparation_codes,
            )

        return selection

    def _has_precipitation(
        self,
        time_slot_weather: TimeSlotWeatherRequest,
    ) -> bool:
        weather_text = " ".join(
            [
                time_slot_weather.currentWeather.precipitationAmount,
                time_slot_weather.currentWeather.precipitationType,
                time_slot_weather.currentWeather.weatherCondition,
                time_slot_weather.currentWeather.skyStatus,
            ]
        ).lower()

        return (
            any(
                keyword in weather_text
                for keyword in ["비", "소나기", "이슬비", "빗방울", "눈"]
            )
            or time_slot_weather.currentWeather.precipitationProbability
            >= 60
        )

    def _has_strong_wind(
        self,
        time_slot_weather: TimeSlotWeatherRequest,
    ) -> bool:
        wind_status = time_slot_weather.currentWeather.windStatus

        return (
            time_slot_weather.currentWeather.windSpeed >= 8
            or "강" in wind_status
            or "센" in wind_status
        )

    def _merge_selection(
        self,
        selection: OutfitSelection,
        *,
        outerwear_code: str | None = None,
        top_code: str | None = None,
        bottom_code: str | None = None,
        shoes_code: str | None = None,
        preparation_codes: list[str] | None = None,
    ) -> OutfitSelection:
        merged_preparation_codes = list(selection.preparationCodes)

        if preparation_codes:
            for code in preparation_codes:
                if code not in merged_preparation_codes:
                    merged_preparation_codes.append(code)

        normalized_preparation_codes = sorted(
            dict.fromkeys(merged_preparation_codes),
            key=lambda code: OutfitCatalog.PREPARATION_PRIORITY.get(code, 99),
        )[:4]

        return selection.model_copy(
            update={
                "outerwearCode": outerwear_code or selection.outerwearCode,
                "topCode": top_code or selection.topCode,
                "bottomCode": bottom_code or selection.bottomCode,
                "shoesCode": shoes_code or selection.shoesCode,
                "preparationCodes": normalized_preparation_codes,
            }
        )
