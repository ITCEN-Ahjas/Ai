from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import OutfitRecommendationResponse


class OutfitRuleEngine:
    def recommend(
        self,
        request: OutfitRecommendationRequest,
    ) -> OutfitRecommendationResponse:
        feels_like_temperature = request.feelsLikeWeather.feelsLikeTemperature

        (
            weather_label,
            outerwear,
            tops,
            bottoms,
            shoes,
            preparation_items,
        ) = self._get_temperature_rule(feels_like_temperature)

        reasons = [
            f"체감온도 {feels_like_temperature:.1f}°C 기준으로 {weather_label}에 맞는 옷차림을 추천합니다."
        ]

        if self._has_rain(request):
            self._extend_unique(
                outerwear,
                ["가벼운 방수 재킷 또는 우비"],
            )
            self._extend_unique(
                shoes,
                ["미끄럼 방지 기능이 있는 운동화"],
            )
            self._extend_unique(
                preparation_items,
                ["접이식 우산", "방수 가방 또는 방수 파우치"],
            )
            reasons.append("비가 예상되어 방수 아우터와 우산을 준비하는 것이 좋습니다.")

        if self._has_snow(request):
            self._extend_unique(
                outerwear,
                ["방수 기능이 있는 두꺼운 아우터"],
            )
            self._extend_unique(
                shoes,
                ["미끄럼 방지 방한화 또는 운동화"],
            )
            self._extend_unique(
                preparation_items,
                ["장갑", "여분 양말"],
            )
            reasons.append("눈 또는 비·눈 예보가 있어 미끄럼 방지 신발과 방한 준비가 필요합니다.")

        if self._has_strong_wind(request):
            self._extend_unique(
                outerwear,
                ["바람을 막아주는 윈드브레이커"],
            )
            self._extend_unique(
                preparation_items,
                ["목도리 또는 얇은 넥워머"],
            )
            reasons.append("바람이 강해 체감온도가 더 낮게 느껴질 수 있습니다.")

        self._apply_travel_style_rule(
            travel_style=request.travelStyle,
            tops=tops,
            shoes=shoes,
            preparation_items=preparation_items,
            reasons=reasons,
        )

        summary = (
            f"{request.region}은(는) 현재 체감온도 "
            f"{feels_like_temperature:.1f}°C로 {weather_label}입니다. "
            f"{request.travelStyle} 일정에 맞춰 활동성과 날씨 변화를 함께 고려한 옷차림을 추천합니다."
        )

        return OutfitRecommendationResponse(
            region=request.region,
            travelStyle=request.travelStyle,
            source="rule",
            summary=summary,
            outerwear=outerwear,
            tops=tops,
            bottoms=bottoms,
            shoes=shoes,
            preparationItems=preparation_items,
            reasons=reasons,
        )

    def _get_temperature_rule(
        self,
        feels_like_temperature: float,
    ) -> tuple[str, list[str], list[str], list[str], list[str], list[str]]:
        if feels_like_temperature >= 28:
            return (
                "더운 날씨",
                ["얇은 가디건 또는 자외선 차단용 셔츠"],
                ["반소매 티셔츠", "통기성이 좋은 상의"],
                ["반바지 또는 얇은 긴바지"],
                ["통풍이 좋은 운동화 또는 샌들"],
                ["자외선 차단제", "모자", "물병"],
            )

        if feels_like_temperature >= 22:
            return (
                "따뜻한 날씨",
                ["얇은 셔츠 또는 가디건"],
                ["반소매 또는 얇은 긴소매 상의"],
                ["가벼운 면바지 또는 청바지"],
                ["편한 운동화"],
                ["물병", "얇은 겉옷"],
            )

        if feels_like_temperature >= 17:
            return (
                "선선한 날씨",
                ["얇은 재킷 또는 가디건"],
                ["긴소매 티셔츠 또는 셔츠"],
                ["긴바지"],
                ["편한 운동화"],
                ["얇은 겉옷", "물병"],
            )

        if feels_like_temperature >= 12:
            return (
                "쌀쌀한 날씨",
                ["가벼운 재킷 또는 바람막이"],
                ["긴소매 티셔츠", "얇은 니트"],
                ["긴바지"],
                ["운동화"],
                ["얇은 목도리", "보온 물병"],
            )

        if feels_like_temperature >= 5:
            return (
                "추운 날씨",
                ["두꺼운 재킷 또는 코트"],
                ["니트 또는 기모 상의"],
                ["기모 바지 또는 두꺼운 긴바지"],
                ["보온 기능이 있는 운동화"],
                ["목도리", "장갑", "보온 물병"],
            )

        return (
            "매우 추운 날씨",
            ["패딩 또는 두꺼운 방한 아우터"],
            ["기모 이너웨어", "두꺼운 니트"],
            ["기모 바지 또는 방한 바지"],
            ["방한화 또는 보온 기능 운동화"],
            ["목도리", "장갑", "핫팩", "보온 물병"],
        )

    def _has_rain(self, request: OutfitRecommendationRequest) -> bool:
        weather_text = self._get_weather_text(request)

        return (
            any(keyword in weather_text for keyword in ["비", "소나기", "이슬비", "빗방울"])
            or request.currentWeather.precipitationProbability >= 60
        )

    def _has_snow(self, request: OutfitRecommendationRequest) -> bool:
        weather_text = self._get_weather_text(request)

        return "눈" in weather_text

    def _has_strong_wind(self, request: OutfitRecommendationRequest) -> bool:
        wind_status = request.currentWeather.windStatus

        return (
            request.currentWeather.windSpeed >= 8
            or "강" in wind_status
            or "센" in wind_status
        )

    def _get_weather_text(self, request: OutfitRecommendationRequest) -> str:
        return " ".join(
            [
                request.currentWeather.precipitationType,
                request.currentWeather.weatherCondition,
                request.currentWeather.skyStatus,
            ]
        )

    def _apply_travel_style_rule(
        self,
        travel_style: str,
        tops: list[str],
        shoes: list[str],
        preparation_items: list[str],
        reasons: list[str],
    ) -> None:
        normalized_style = travel_style.replace(" ", "")

        if any(keyword in normalized_style for keyword in ["레포츠", "체험", "액티비티"]):
            self._extend_unique(
                tops,
                ["활동성이 좋은 기능성 상의"],
            )
            self._extend_unique(
                shoes,
                ["발을 안정적으로 잡아주는 운동화"],
            )
            self._extend_unique(
                preparation_items,
                ["여분 양말"],
            )
            reasons.append("활동량이 많은 일정에 맞춰 움직이기 편한 상의와 운동화를 추천합니다.")
            return

        if any(keyword in normalized_style for keyword in ["자연", "등산", "트레킹"]):
            self._extend_unique(
                tops,
                ["햇빛과 체온 변화에 대응할 수 있는 얇은 긴소매 상의"],
            )
            self._extend_unique(
                shoes,
                ["바닥 접지력이 좋은 운동화"],
            )
            self._extend_unique(
                preparation_items,
                ["모자", "휴대용 벌레 기피제"],
            )
            reasons.append("자연 관광 또는 야외 이동 일정에 맞춰 긴소매 상의와 접지력 좋은 신발을 추천합니다.")
            return

        if any(keyword in normalized_style for keyword in ["축제", "행사", "공연"]):
            self._extend_unique(
                shoes,
                ["오래 걸어도 편한 운동화"],
            )
            self._extend_unique(
                preparation_items,
                ["보조배터리", "가벼운 크로스백"],
            )
            reasons.append("축제와 행사 관람은 대기와 이동 시간이 길 수 있어 편한 신발을 추천합니다.")
            return

        self._extend_unique(
            shoes,
            ["오래 걸어도 편한 운동화"],
        )
        self._extend_unique(
            preparation_items,
            ["가벼운 가방"],
        )
        reasons.append("관광 이동을 고려해 오래 걸어도 편한 신발을 추천합니다.")

    def _extend_unique(
        self,
        target: list[str],
        values: list[str],
    ) -> None:
        for value in values:
            if value not in target:
                target.append(value)