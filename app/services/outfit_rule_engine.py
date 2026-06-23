from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import (OutfitRecommendationResponse,
                                         OutfitSelection)
from app.services.outfit_catalog import OutfitCatalog


class OutfitRuleEngine:
    def recommend(
        self,
        request: OutfitRecommendationRequest,
    ) -> OutfitRecommendationResponse:
        selection = self.select(request)

        return OutfitCatalog().build_response(
            region=request.region,
            travel_style=request.travelStyle,
            selection=selection,
            source="fallback",
        )

    def select(
        self,
        request: OutfitRecommendationRequest,
    ) -> OutfitSelection:
        feels_like_temperature = request.feelsLikeWeather.feelsLikeTemperature
        selection = self._select_temperature_base(feels_like_temperature)

        if self._has_snow(request):
            selection = self._replace_selection(
                selection,
                outerwear_code="waterproof_winter_outerwear",
                top_code="thermal_inner",
                bottom_code="winter_pants",
                shoes_code="anti_slip_winter_boots",
                preparation_codes=[
                    "warm_accessory",
                    "hot_pack",
                    "extra_socks",
                    "thermal_bottle",
                ],
            )
        elif self._has_actual_rain(request):
            selection = self._replace_selection(
                selection,
                outerwear_code="waterproof_jacket",
                shoes_code="rain_boots",
                preparation_codes=[
                    "umbrella",
                    "waterproof_pouch",
                    "extra_socks",
                ],
            )
        elif self._has_rain_risk(request):
            selection = self._replace_selection(
                selection,
                outerwear_code="waterproof_jacket",
                shoes_code="waterproof_sneakers",
                preparation_codes=["umbrella", "waterproof_pouch"],
            )

        if self._has_strong_wind(request) and not self._has_precipitation(
            request
        ):
            if feels_like_temperature < 22:
                selection = self._replace_selection(
                    selection,
                    outerwear_code="windbreaker",
                    preparation_codes=["light_outerwear"],
                )

        return self._apply_travel_style_rule(request, selection)

    def _select_temperature_base(
        self,
        feels_like_temperature: float,
    ) -> OutfitSelection:
        if feels_like_temperature >= 30:
            return OutfitSelection(
                outerwearCode="no_outer",
                topCode="short_sleeve_tshirt",
                bottomCode="shorts",
                shoesCode="sandals",
                preparationCodes=[
                    "sunscreen",
                    "hat",
                    "water_bottle",
                    "portable_fan",
                ],
            )

        if feels_like_temperature >= 26:
            return OutfitSelection(
                outerwearCode="uv_shirt",
                topCode="short_sleeve_tshirt",
                bottomCode="lightweight_pants",
                shoesCode="breathable_sneakers",
                preparationCodes=["sunscreen", "hat", "water_bottle"],
            )

        if feels_like_temperature >= 22:
            return OutfitSelection(
                outerwearCode="light_shirt",
                topCode="short_sleeve_shirt",
                bottomCode="cotton_pants",
                shoesCode="sneakers",
                preparationCodes=["light_outerwear", "water_bottle"],
            )

        if feels_like_temperature >= 17:
            return OutfitSelection(
                outerwearCode="light_cardigan",
                topCode="long_sleeve_tshirt",
                bottomCode="cotton_pants",
                shoesCode="sneakers",
                preparationCodes=["light_outerwear", "water_bottle"],
            )

        if feels_like_temperature >= 12:
            return OutfitSelection(
                outerwearCode="light_jacket",
                topCode="long_sleeve_tshirt",
                bottomCode="jeans",
                shoesCode="sneakers",
                preparationCodes=["light_outerwear", "water_bottle"],
            )

        if feels_like_temperature >= 5:
            return OutfitSelection(
                outerwearCode="heavy_jacket",
                topCode="knit",
                bottomCode="brushed_pants",
                shoesCode="insulated_sneakers",
                preparationCodes=["warm_accessory", "thermal_bottle"],
            )

        return OutfitSelection(
            outerwearCode="padded_outerwear",
            topCode="thermal_inner",
            bottomCode="winter_pants",
            shoesCode="anti_slip_winter_boots",
            preparationCodes=[
                "warm_accessory",
                "hot_pack",
                "thermal_bottle",
            ],
        )

    def _apply_travel_style_rule(
        self,
        request: OutfitRecommendationRequest,
        selection: OutfitSelection,
    ) -> OutfitSelection:
        travel_style = request.travelStyle

        if travel_style == "많이 걷는 여행":
            return self._replace_selection(
                selection,
                shoes_code=self._get_walking_shoes(request),
                preparation_codes=["water_bottle", "battery"],
            )

        if travel_style == "야외 활동":
            outdoor_preparations = ["water_bottle", "hat"]

            if request.feelsLikeWeather.feelsLikeTemperature >= 17:
                outdoor_preparations.append("insect_repellent")

            return self._replace_selection(
                selection,
                shoes_code=self._get_outdoor_shoes(request),
                bottom_code=(
                    "water_repellent_pants"
                    if self._has_precipitation(request)
                    else "training_pants"
                ),
                preparation_codes=outdoor_preparations,
            )

        if travel_style == "실내 중심":
            return self._replace_selection(
                selection,
                outerwear_code=(
                    "light_cardigan"
                    if request.feelsLikeWeather.feelsLikeTemperature >= 17
                    else selection.outerwearCode
                ),
                preparation_codes=["light_outerwear", "battery"],
            )

        if travel_style == "야간 일정":
            outerwear_code = selection.outerwearCode

            if request.feelsLikeWeather.feelsLikeTemperature >= 17:
                outerwear_code = "light_jacket"

            return self._replace_selection(
                selection,
                outerwear_code=outerwear_code,
                preparation_codes=["light_outerwear", "battery"],
            )

        if travel_style == "비 오는 날 대비":
            return self._replace_selection(
                selection,
                outerwear_code="waterproof_jacket",
                shoes_code=(
                    "rain_boots"
                    if self._has_actual_rain(request)
                    else "waterproof_sneakers"
                ),
                preparation_codes=[
                    "umbrella",
                    "waterproof_pouch",
                    "extra_socks",
                ],
            )

        return selection

    def _get_walking_shoes(
        self,
        request: OutfitRecommendationRequest,
    ) -> str:
        if self._has_snow(request):
            return "anti_slip_winter_boots"

        if self._has_actual_rain(request):
            return "waterproof_hiking_shoes"

        if self._has_rain_risk(request):
            return "waterproof_sneakers"

        return "cushioned_sneakers"

    def _get_outdoor_shoes(
        self,
        request: OutfitRecommendationRequest,
    ) -> str:
        if self._has_snow(request):
            return "anti_slip_winter_boots"

        if self._has_precipitation(request):
            return "waterproof_hiking_shoes"

        return "grip_sneakers"

    def _replace_selection(
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

    def _has_actual_rain(
        self,
        request: OutfitRecommendationRequest,
    ) -> bool:
        return any(
            keyword in self._get_weather_text(request)
            for keyword in ["비", "소나기", "이슬비", "빗방울"]
        )

    def _has_rain_risk(
        self,
        request: OutfitRecommendationRequest,
    ) -> bool:
        return request.currentWeather.precipitationProbability >= 60

    def _has_snow(
        self,
        request: OutfitRecommendationRequest,
    ) -> bool:
        return "눈" in self._get_weather_text(request)

    def _has_strong_wind(
        self,
        request: OutfitRecommendationRequest,
    ) -> bool:
        wind_status = request.currentWeather.windStatus

        return (
            request.currentWeather.windSpeed >= 8
            or "강" in wind_status
            or "센" in wind_status
        )

    def _has_precipitation(
        self,
        request: OutfitRecommendationRequest,
    ) -> bool:
        return (
            self._has_actual_rain(request)
            or self._has_snow(request)
            or self._has_rain_risk(request)
        )

    def _get_weather_text(
        self,
        request: OutfitRecommendationRequest,
    ) -> str:
        return " ".join(
            [
                request.currentWeather.precipitationAmount,
                request.currentWeather.precipitationType,
                request.currentWeather.weatherCondition,
                request.currentWeather.skyStatus,
            ]
        ).lower()