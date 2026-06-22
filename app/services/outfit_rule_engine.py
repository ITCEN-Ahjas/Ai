from app.schemas.outfit_request import OutfitRecommendationRequest
from app.schemas.outfit_response import (OutfitCard, OutfitCards,
                                         OutfitRecommendationResponse,
                                         PreparationItem)


class OutfitRuleEngine:
    PREPARATION_PRIORITY = {
        "umbrella": 1,
        "waterproof_pouch": 2,
        "warm_accessory": 3,
        "hot_pack": 4,
        "extra_socks": 5,
        "light_outerwear": 6,
        "comfortable_shoes": 7,
        "water_bottle": 8,
        "battery": 9,
        "sunscreen": 10,
        "hat": 11,
        "insect_repellent": 12,
    }

    def recommend(
        self,
        request: OutfitRecommendationRequest,
    ) -> OutfitRecommendationResponse:
        outfit_cards, preparation_items = self._get_temperature_rule(
            request.feelsLikeWeather.feelsLikeTemperature
        )

        if self._has_rain(request):
            outfit_cards.outerwear = OutfitCard(
                name="방수 재킷 / 우비",
                description="비를 막아 야외 이동 중 옷이 젖는 것을 줄여줘요.",
            )
            outfit_cards.shoes = OutfitCard(
                name="미끄럼 방지 운동화",
                description="젖은 길에서도 비교적 안정적으로 걸을 수 있어요.",
            )
            self._add_preparation(
                preparation_items,
                code="umbrella",
                name="작은 우산",
                description="갑작스러운 비를 대비해요.",
            )
            self._add_preparation(
                preparation_items,
                code="waterproof_pouch",
                name="방수 파우치",
                description="휴대폰과 소지품이 젖지 않도록 보관해요.",
            )

        if self._has_snow(request):
            outfit_cards.outerwear = OutfitCard(
                name="방수 방한 아우터",
                description="눈과 낮은 체감온도에 대비할 수 있어요.",
            )
            outfit_cards.shoes = OutfitCard(
                name="미끄럼 방지 방한화",
                description="눈길이나 젖은 바닥에서 이동할 때 도움이 돼요.",
            )
            self._add_preparation(
                preparation_items,
                code="warm_accessory",
                name="목도리 / 장갑",
                description="노출되는 부위를 따뜻하게 보호해요.",
            )
            self._add_preparation(
                preparation_items,
                code="extra_socks",
                name="여분 양말",
                description="발이 젖었을 때 갈아 신기 좋아요.",
            )

        if self._has_strong_wind(request) and not self._has_rain(request):
            outfit_cards.outerwear = OutfitCard(
                name="바람막이 / 윈드브레이커",
                description="강한 바람을 막아 체감온도가 낮아지는 것을 줄여줘요.",
            )
            self._add_preparation(
                preparation_items,
                code="light_outerwear",
                name="얇은 겉옷",
                description="바람이 강해질 때 바로 걸칠 수 있어요.",
            )

        self._apply_travel_style_rule(
            travel_style=request.travelStyle,
            outfit_cards=outfit_cards,
            preparation_items=preparation_items,
        )

        return OutfitRecommendationResponse(
            region=request.region,
            travelStyle=request.travelStyle,
            source="fallback",
            outfitCards=outfit_cards,
            preparationItems=self._sort_and_limit_preparations(preparation_items),
        )

    def _get_temperature_rule(
        self,
        feels_like_temperature: float,
    ) -> tuple[OutfitCards, list[PreparationItem]]:
        if feels_like_temperature >= 28:
            return (
                OutfitCards(
                    outerwear=OutfitCard(
                        name="얇은 가디건 / 자외선 차단 셔츠",
                        description="강한 햇빛이나 실내 냉방에 가볍게 대응할 수 있어요.",
                    ),
                    top=OutfitCard(
                        name="반소매 티셔츠",
                        description="더운 날씨에 통기성이 좋아 편안해요.",
                    ),
                    bottom=OutfitCard(
                        name="반바지 / 얇은 긴바지",
                        description="활동성과 시원함을 함께 고려한 선택이에요.",
                    ),
                    shoes=OutfitCard(
                        name="통풍 좋은 운동화 / 샌들",
                        description="오래 걸을 때 발의 답답함을 줄여줘요.",
                    ),
                ),
                [
                    PreparationItem(
                        code="sunscreen",
                        name="자외선 차단제",
                        description="장시간 야외 활동 전 챙기세요.",
                    ),
                    PreparationItem(
                        code="hat",
                        name="모자",
                        description="햇빛을 가리고 더위를 줄여줘요.",
                    ),
                    PreparationItem(
                        code="water_bottle",
                        name="물병",
                        description="수분 보충을 위해 챙기세요.",
                    ),
                ],
            )

        if feels_like_temperature >= 22:
            return (
                OutfitCards(
                    outerwear=OutfitCard(
                        name="얇은 셔츠 / 가디건",
                        description="아침저녁 기온 변화에 가볍게 걸치기 좋아요.",
                    ),
                    top=OutfitCard(
                        name="반소매 / 얇은 긴소매",
                        description="낮 기온에 맞춰 편안하게 입을 수 있어요.",
                    ),
                    bottom=OutfitCard(
                        name="면바지 / 청바지",
                        description="여행 중 활동하기 편한 기본 하의예요.",
                    ),
                    shoes=OutfitCard(
                        name="운동화 / 스니커즈",
                        description="관광지 이동과 장시간 걷기에 편안해요.",
                    ),
                ),
                [
                    PreparationItem(
                        code="light_outerwear",
                        name="얇은 겉옷",
                        description="기온이 내려갈 때 바로 걸칠 수 있어요.",
                    ),
                    PreparationItem(
                        code="water_bottle",
                        name="물병",
                        description="수분 보충을 위해 챙기세요.",
                    ),
                ],
            )

        if feels_like_temperature >= 17:
            return (
                OutfitCards(
                    outerwear=OutfitCard(
                        name="얇은 바람막이 / 가디건",
                        description="선선한 바람과 일교차에 대응하기 좋아요.",
                    ),
                    top=OutfitCard(
                        name="긴팔 티셔츠 / 셔츠",
                        description="낮과 저녁 모두 편하게 입을 수 있어요.",
                    ),
                    bottom=OutfitCard(
                        name="면바지 / 청바지",
                        description="활동성과 보온성을 함께 고려한 선택이에요.",
                    ),
                    shoes=OutfitCard(
                        name="운동화 / 스니커즈",
                        description="장시간 걷기에도 편안한 신발이에요.",
                    ),
                ),
                [
                    PreparationItem(
                        code="light_outerwear",
                        name="얇은 겉옷",
                        description="날씨 변화에 맞춰 쉽게 걸칠 수 있어요.",
                    ),
                    PreparationItem(
                        code="water_bottle",
                        name="물병",
                        description="여행 중 수분 보충을 위해 챙기세요.",
                    ),
                ],
            )

        if feels_like_temperature >= 12:
            return (
                OutfitCards(
                    outerwear=OutfitCard(
                        name="얇은 바람막이 / 점퍼",
                        description="일교차를 막아 체감온도를 유지해줘요.",
                    ),
                    top=OutfitCard(
                        name="긴팔 티셔츠 / 니트",
                        description="쌀쌀한 날씨에 보온성을 높여줘요.",
                    ),
                    bottom=OutfitCard(
                        name="면바지 / 청바지",
                        description="활동하기 편하고 보온성도 적당해요.",
                    ),
                    shoes=OutfitCard(
                        name="운동화 / 스니커즈",
                        description="장시간 걷기에도 편안한 신발이에요.",
                    ),
                ),
                [
                    PreparationItem(
                        code="light_outerwear",
                        name="얇은 겉옷",
                        description="아침저녁 쌀쌀할 때 유용해요.",
                    ),
                    PreparationItem(
                        code="water_bottle",
                        name="물병",
                        description="여행 중 수분 보충을 위해 챙기세요.",
                    ),
                ],
            )

        if feels_like_temperature >= 5:
            return (
                OutfitCards(
                    outerwear=OutfitCard(
                        name="두꺼운 재킷 / 코트",
                        description="낮은 체감온도에서 몸을 따뜻하게 유지해줘요.",
                    ),
                    top=OutfitCard(
                        name="니트 / 기모 상의",
                        description="추운 날씨에 보온성을 높여줘요.",
                    ),
                    bottom=OutfitCard(
                        name="기모 바지 / 두꺼운 긴바지",
                        description="하체 보온을 유지하기 좋아요.",
                    ),
                    shoes=OutfitCard(
                        name="보온 운동화",
                        description="차가운 바닥과 낮은 기온에 대비할 수 있어요.",
                    ),
                ),
                [
                    PreparationItem(
                        code="warm_accessory",
                        name="목도리 / 장갑",
                        description="바람이 부는 날 체온 유지에 도움이 돼요.",
                    ),
                    PreparationItem(
                        code="water_bottle",
                        name="물병",
                        description="따뜻한 음료나 물을 준비할 수 있어요.",
                    ),
                ],
            )

        return (
            OutfitCards(
                outerwear=OutfitCard(
                    name="패딩 / 방한 아우터",
                    description="매우 낮은 체감온도에 대비해 보온성을 높여줘요.",
                ),
                top=OutfitCard(
                    name="기모 이너웨어 / 두꺼운 니트",
                    description="겹쳐 입어 체온을 유지하기 좋아요.",
                ),
                bottom=OutfitCard(
                    name="기모 바지 / 방한 바지",
                    description="추운 야외 이동 중 하체 보온에 도움이 돼요.",
                ),
                shoes=OutfitCard(
                    name="방한화 / 보온 운동화",
                    description="발이 차가워지는 것을 줄여줘요.",
                ),
            ),
            [
                PreparationItem(
                    code="warm_accessory",
                    name="목도리 / 장갑",
                    description="노출되는 부위를 따뜻하게 보호해요.",
                ),
                PreparationItem(
                    code="hot_pack",
                    name="핫팩",
                    description="추운 야외 일정에서 유용해요.",
                ),
                PreparationItem(
                    code="water_bottle",
                    name="보온 물병",
                    description="따뜻한 음료를 준비할 수 있어요.",
                ),
            ],
        )

    def _apply_travel_style_rule(
        self,
        travel_style: str,
        outfit_cards: OutfitCards,
        preparation_items: list[PreparationItem],
    ) -> None:
        if travel_style == "많이 걷는 여행":
            outfit_cards.shoes = OutfitCard(
                name="운동화 / 스니커즈",
                description="장시간 걷기에도 발이 편안한 신발을 추천해요.",
            )
            self._add_preparation(
                preparation_items,
                code="comfortable_shoes",
                name="편한 신발",
                description="많이 걷는 일정에 대비해 발이 편한 신발이 좋아요.",
            )
            self._add_preparation(
                preparation_items,
                code="water_bottle",
                name="물병",
                description="걷는 중 수분 보충을 위해 챙기세요.",
            )
            return

        if travel_style == "야외 활동":
            outfit_cards.shoes = OutfitCard(
                name="접지력 좋은 운동화",
                description="야외 이동과 활동 중 발을 안정적으로 잡아줘요.",
            )
            self._add_preparation(
                preparation_items,
                code="hat",
                name="모자",
                description="햇빛이나 가벼운 비를 피하는 데 도움이 돼요.",
            )
            self._add_preparation(
                preparation_items,
                code="insect_repellent",
                name="벌레 기피제",
                description="자연 관광지나 야외 활동에서 유용해요.",
            )
            return

        if travel_style == "실내 중심":
            self._add_preparation(
                preparation_items,
                code="light_outerwear",
                name="얇은 겉옷",
                description="실내 냉방이나 외부 기온 변화에 대비해요.",
            )
            return

        if travel_style == "야간 일정":
            self._add_preparation(
                preparation_items,
                code="light_outerwear",
                name="얇은 겉옷",
                description="해가 진 뒤 기온이 낮아질 때 유용해요.",
            )
            self._add_preparation(
                preparation_items,
                code="battery",
                name="보조배터리",
                description="야간 이동과 사진 촬영을 위해 준비하세요.",
            )
            return

        if travel_style == "비 오는 날 대비":
            outfit_cards.outerwear = OutfitCard(
                name="방수 재킷 / 우비",
                description="비가 오거나 날씨가 바뀔 때 대비하기 좋아요.",
            )
            outfit_cards.shoes = OutfitCard(
                name="미끄럼 방지 운동화",
                description="젖은 길에서도 이동하기 편안한 신발이에요.",
            )
            self._add_preparation(
                preparation_items,
                code="umbrella",
                name="작은 우산",
                description="갑작스러운 비를 대비해요.",
            )
            self._add_preparation(
                preparation_items,
                code="waterproof_pouch",
                name="방수 파우치",
                description="휴대폰과 소지품을 젖지 않게 보관해요.",
            )

    def _has_rain(self, request: OutfitRecommendationRequest) -> bool:
        weather_text = self._get_weather_text(request)

        return (
            any(
                keyword in weather_text
                for keyword in ["비", "소나기", "이슬비", "빗방울"]
            )
            or request.currentWeather.precipitationProbability >= 60
        )

    def _has_snow(self, request: OutfitRecommendationRequest) -> bool:
        return "눈" in self._get_weather_text(request)

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

    def _add_preparation(
        self,
        preparation_items: list[PreparationItem],
        code: str,
        name: str,
        description: str,
    ) -> None:
        if any(item.code == code for item in preparation_items):
            return

        preparation_items.append(
            PreparationItem(
                code=code,
                name=name,
                description=description,
            )
        )

    def _sort_and_limit_preparations(
        self,
        preparation_items: list[PreparationItem],
    ) -> list[PreparationItem]:
        return sorted(
            preparation_items,
            key=lambda item: self.PREPARATION_PRIORITY.get(item.code, 99),
        )[:4]