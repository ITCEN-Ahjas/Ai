from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import OutfitSelection
from app.schemas.outfit_time_slot_request import TimeSlotWeatherRequest
from app.services.outfit_catalog import OutfitCatalog
from app.services.outfit_rule_engine import OutfitRuleEngine


class TimeSlotOutfitRuleEngine:
    def __init__(self) -> None:
        self._base_rule_engine = OutfitRuleEngine()

    def select(
        self,
        *,
        region: str,
        time_slot_weather: TimeSlotWeatherRequest,
    ) -> OutfitSelection:
        base_request = OutfitRecommendationRequest(
            region=region,
            travelStyle="기본 추천",
            currentWeather=time_slot_weather.currentWeather,
            feelsLikeWeather=time_slot_weather.feelsLikeWeather,
        )

        selection = self._base_rule_engine.select(base_request)

        return self._apply_time_slot_rule(
            time_slot_weather=time_slot_weather,
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

    def _merge_selection(
        self,
        selection: OutfitSelection,
        *,
        outerwear_code: str | None = None,
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
                "preparationCodes": normalized_preparation_codes,
            }
        )
