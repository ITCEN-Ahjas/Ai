from dataclasses import dataclass
from typing import Literal

from app.schemas.outfit_response import (OutfitCard, OutfitCards,
                                         OutfitRecommendationResponse,
                                         OutfitSelection, PreparationItem)


class InvalidOutfitSelectionError(ValueError):
    pass


@dataclass(frozen=True)
class CatalogEntry:
    code: str
    name: str
    description: str


class OutfitCatalog:
    OUTFIT_CATALOG = {
        "outerwear": {
            "no_outer": CatalogEntry(
                code="no_outer",
                name="별도 아우터 없이 가볍게 이동",
                description="낮 기온이 높아 두꺼운 겉옷 없이 여행하기 좋아요.",
            ),
            "uv_shirt": CatalogEntry(
                code="uv_shirt",
                name="얇은 셔츠 / 자외선 차단 셔츠",
                description="강한 햇빛과 실내 냉방에 가볍게 대응하기 좋아요.",
            ),
            "light_cardigan": CatalogEntry(
                code="light_cardigan",
                name="얇은 가디건",
                description="아침저녁 기온 변화에 가볍게 걸치기 좋아요.",
            ),
            "light_shirt": CatalogEntry(
                code="light_shirt",
                name="얇은 셔츠",
                description="덥지 않으면서 햇빛과 바람을 가볍게 막아줘요.",
            ),
            "windbreaker": CatalogEntry(
                code="windbreaker",
                name="바람막이 / 윈드브레이커",
                description="바람으로 체감온도가 낮아지는 것을 줄여줘요.",
            ),
            "light_jacket": CatalogEntry(
                code="light_jacket",
                name="얇은 점퍼 / 가벼운 재킷",
                description="선선한 날씨와 일교차에 대응하기 좋아요.",
            ),
            "trench_coat": CatalogEntry(
                code="trench_coat",
                name="트렌치코트 / 두꺼운 재킷",
                description="쌀쌀한 야외 이동에서 보온성을 높여줘요.",
            ),
            "waterproof_jacket": CatalogEntry(
                code="waterproof_jacket",
                name="방수 재킷 / 우비",
                description="비가 오는 날 옷이 젖는 것을 줄여줘요.",
            ),
            "heavy_jacket": CatalogEntry(
                code="heavy_jacket",
                name="두꺼운 재킷 / 코트",
                description="낮은 체감온도에서 몸을 따뜻하게 유지해줘요.",
            ),
            "padded_outerwear": CatalogEntry(
                code="padded_outerwear",
                name="패딩 / 방한 아우터",
                description="매우 낮은 체감온도에 대비해 보온성을 높여줘요.",
            ),
            "waterproof_winter_outerwear": CatalogEntry(
                code="waterproof_winter_outerwear",
                name="방수 방한 아우터",
                description="눈과 낮은 체감온도에 함께 대비하기 좋아요.",
            ),
        },
        "top": {
            "short_sleeve_tshirt": CatalogEntry(
                code="short_sleeve_tshirt",
                name="반소매 티셔츠",
                description="더운 날씨에 통기성이 좋아 편안하게 입을 수 있어요.",
            ),
            "short_sleeve_shirt": CatalogEntry(
                code="short_sleeve_shirt",
                name="반소매 셔츠",
                description="답답하지 않으면서 여행지에서 단정하게 입기 좋아요.",
            ),
            "light_long_sleeve": CatalogEntry(
                code="light_long_sleeve",
                name="얇은 긴소매 티셔츠",
                description="햇빛과 약한 바람을 함께 피하기 좋아요.",
            ),
            "long_sleeve_tshirt": CatalogEntry(
                code="long_sleeve_tshirt",
                name="긴팔 티셔츠",
                description="낮과 저녁 모두 편하게 입을 수 있는 기본 상의예요.",
            ),
            "shirt": CatalogEntry(
                code="shirt",
                name="긴팔 셔츠",
                description="기온 변화에 맞춰 단독 또는 겹쳐 입기 좋아요.",
            ),
            "sweatshirt": CatalogEntry(
                code="sweatshirt",
                name="맨투맨",
                description="선선한 날씨에 편안한 보온감을 더해줘요.",
            ),
            "knit": CatalogEntry(
                code="knit",
                name="니트",
                description="쌀쌀한 날씨에 체온을 유지하기 좋아요.",
            ),
            "brushed_top": CatalogEntry(
                code="brushed_top",
                name="기모 상의",
                description="추운 날 야외 이동에서 보온성을 높여줘요.",
            ),
            "thermal_inner": CatalogEntry(
                code="thermal_inner",
                name="기모 이너웨어 / 두꺼운 니트",
                description="매우 추운 날에는 겹쳐 입어 체온을 유지해요.",
            ),
        },
        "bottom": {
            "shorts": CatalogEntry(
                code="shorts",
                name="반바지",
                description="더운 날씨에 시원하고 활동하기 편해요.",
            ),
            "lightweight_pants": CatalogEntry(
                code="lightweight_pants",
                name="얇은 긴바지",
                description="햇빛과 실내 냉방을 함께 대비하기 좋아요.",
            ),
            "cotton_pants": CatalogEntry(
                code="cotton_pants",
                name="면바지",
                description="여행 중 오래 움직여도 편안한 기본 하의예요.",
            ),
            "jeans": CatalogEntry(
                code="jeans",
                name="청바지",
                description="가벼운 관광과 도심 이동에 무난하게 입기 좋아요.",
            ),
            "jogger_pants": CatalogEntry(
                code="jogger_pants",
                name="조거 팬츠",
                description="많이 걷거나 활동하는 일정에 편안해요.",
            ),
            "training_pants": CatalogEntry(
                code="training_pants",
                name="트레이닝 팬츠",
                description="야외 활동에서 움직임이 편안한 하의예요.",
            ),
            "brushed_pants": CatalogEntry(
                code="brushed_pants",
                name="기모 바지",
                description="쌀쌀한 날 하체 보온을 유지하기 좋아요.",
            ),
            "winter_pants": CatalogEntry(
                code="winter_pants",
                name="방한 바지",
                description="매우 추운 야외 일정에서 하체를 따뜻하게 보호해요.",
            ),
            "water_repellent_pants": CatalogEntry(
                code="water_repellent_pants",
                name="생활 방수 바지",
                description="비가 오거나 젖은 길을 걸을 때 부담을 줄여줘요.",
            ),
        },
        "shoes": {
            "sandals": CatalogEntry(
                code="sandals",
                name="샌들",
                description="매우 더운 날 짧은 이동에 시원하게 신기 좋아요.",
            ),
            "breathable_sneakers": CatalogEntry(
                code="breathable_sneakers",
                name="통풍 좋은 운동화",
                description="더운 날 오래 걸을 때 발의 답답함을 줄여줘요.",
            ),
            "sneakers": CatalogEntry(
                code="sneakers",
                name="기본 운동화 / 스니커즈",
                description="관광지 이동과 일상적인 여행 일정에 편안해요.",
            ),
            "cushioned_sneakers": CatalogEntry(
                code="cushioned_sneakers",
                name="쿠션 운동화",
                description="많이 걷는 여행에서 발의 피로를 줄이는 데 도움이 돼요.",
            ),
            "grip_sneakers": CatalogEntry(
                code="grip_sneakers",
                name="접지력 좋은 운동화",
                description="야외 활동과 울퉁불퉁한 길에서 안정적으로 걸을 수 있어요.",
            ),
            "waterproof_sneakers": CatalogEntry(
                code="waterproof_sneakers",
                name="생활 방수 운동화",
                description="비가 올 가능성이 있을 때 발이 젖는 것을 줄여줘요.",
            ),
            "rain_boots": CatalogEntry(
                code="rain_boots",
                name="짧은 장화 / 레인부츠",
                description="비가 오는 날 젖은 길과 물웅덩이 이동에 적합해요.",
            ),
            "waterproof_hiking_shoes": CatalogEntry(
                code="waterproof_hiking_shoes",
                name="방수 트레킹화",
                description="비 오는 야외 활동에서 발을 안정적으로 보호해줘요.",
            ),
            "insulated_sneakers": CatalogEntry(
                code="insulated_sneakers",
                name="보온 운동화",
                description="추운 날 차가운 바닥으로부터 발을 보호해줘요.",
            ),
            "anti_slip_winter_boots": CatalogEntry(
                code="anti_slip_winter_boots",
                name="미끄럼 방지 방한화",
                description="눈길이나 결빙 구간에서 미끄러짐을 줄이는 데 도움이 돼요.",
            ),
        },
    }

    PREPARATION_CATALOG = {
        "umbrella": CatalogEntry(
            code="umbrella",
            name="작은 우산",
            description="갑작스러운 비를 대비해 가방에 넣어 두세요.",
        ),
        "waterproof_pouch": CatalogEntry(
            code="waterproof_pouch",
            name="방수 파우치",
            description="휴대폰과 소지품이 젖지 않도록 보관해요.",
        ),
        "extra_socks": CatalogEntry(
            code="extra_socks",
            name="여분 양말",
            description="발이 젖었을 때 갈아 신기 좋아요.",
        ),
        "light_outerwear": CatalogEntry(
            code="light_outerwear",
            name="얇은 겉옷",
            description="아침저녁이나 실내 냉방에 바로 걸치기 좋아요.",
        ),
        "warm_accessory": CatalogEntry(
            code="warm_accessory",
            name="목도리 / 장갑",
            description="바람이 부는 날 노출 부위를 따뜻하게 보호해요.",
        ),
        "hot_pack": CatalogEntry(
            code="hot_pack",
            name="핫팩",
            description="추운 야외 일정에서 손과 몸을 데우는 데 유용해요.",
        ),
        "water_bottle": CatalogEntry(
            code="water_bottle",
            name="물병",
            description="관광지 이동 중 수분을 보충할 수 있어요.",
        ),
        "thermal_bottle": CatalogEntry(
            code="thermal_bottle",
            name="보온 물병",
            description="추운 날 따뜻한 음료를 준비하기 좋아요.",
        ),
        "battery": CatalogEntry(
            code="battery",
            name="보조배터리",
            description="야간 이동과 사진 촬영을 위해 챙기세요.",
        ),
        "sunscreen": CatalogEntry(
            code="sunscreen",
            name="자외선 차단제",
            description="장시간 야외 활동 전 미리 발라 주세요.",
        ),
        "hat": CatalogEntry(
            code="hat",
            name="모자",
            description="강한 햇빛이나 가벼운 비를 피하는 데 도움이 돼요.",
        ),
        "insect_repellent": CatalogEntry(
            code="insect_repellent",
            name="벌레 기피제",
            description="자연 관광지와 야외 활동에서 유용해요.",
        ),
        "portable_fan": CatalogEntry(
            code="portable_fan",
            name="휴대용 선풍기",
            description="더운 날 야외 대기 시간에 시원함을 더해줘요.",
        ),
    }

    PREPARATION_PRIORITY = {
        "umbrella": 1,
        "waterproof_pouch": 2,
        "extra_socks": 3,
        "warm_accessory": 4,
        "hot_pack": 5,
        "thermal_bottle": 6,
        "light_outerwear": 7,
        "water_bottle": 8,
        "battery": 9,
        "sunscreen": 10,
        "hat": 11,
        "insect_repellent": 12,
        "portable_fan": 13,
    }

    def build_response(
        self,
        *,
        region: str,
        travel_style: str,
        selection: OutfitSelection,
        source: Literal["ai", "fallback"],
    ) -> OutfitRecommendationResponse:
        normalized_selection = self.validate_selection(selection)

        return OutfitRecommendationResponse(
            region=region,
            travelStyle=travel_style,
            source=source,
            outfitCards=OutfitCards(
                outerwear=self._to_outfit_card(
                    "outerwear",
                    normalized_selection.outerwearCode,
                ),
                top=self._to_outfit_card(
                    "top",
                    normalized_selection.topCode,
                ),
                bottom=self._to_outfit_card(
                    "bottom",
                    normalized_selection.bottomCode,
                ),
                shoes=self._to_outfit_card(
                    "shoes",
                    normalized_selection.shoesCode,
                ),
            ),
            preparationItems=self._to_preparation_items(
                normalized_selection.preparationCodes,
            ),
        )

    def validate_selection(self, selection: OutfitSelection) -> OutfitSelection:
        self._require_outfit_code("outerwear", selection.outerwearCode)
        self._require_outfit_code("top", selection.topCode)
        self._require_outfit_code("bottom", selection.bottomCode)
        self._require_outfit_code("shoes", selection.shoesCode)

        for code in selection.preparationCodes:
            if code not in self.PREPARATION_CATALOG:
                raise InvalidOutfitSelectionError(
                    f"지원하지 않는 준비물 코드입니다: {code}"
                )

        preparation_codes = self._sort_and_limit_codes(
            selection.preparationCodes,
        )

        return selection.model_copy(
            update={"preparationCodes": preparation_codes},
        )

    def get_prompt_catalog(self) -> str:
        sections = []

        for category, items in self.OUTFIT_CATALOG.items():
            item_lines = [
                f"- {entry.code}: {entry.name}"
                for entry in items.values()
            ]
            sections.append(f"[{category}]\n" + "\n".join(item_lines))

        preparation_lines = [
            f"- {entry.code}: {entry.name}"
            for entry in self.PREPARATION_CATALOG.values()
        ]
        sections.append("[preparation]\n" + "\n".join(preparation_lines))

        return "\n\n".join(sections)

    def _to_outfit_card(self, category: str, code: str) -> OutfitCard:
        entry = self.OUTFIT_CATALOG[category][code]

        return OutfitCard(
            code=entry.code,
            name=entry.name,
            description=entry.description,
        )

    def _to_preparation_items(
        self,
        preparation_codes: list[str],
    ) -> list[PreparationItem]:
        return [
            PreparationItem(
                code=self.PREPARATION_CATALOG[code].code,
                name=self.PREPARATION_CATALOG[code].name,
                description=self.PREPARATION_CATALOG[code].description,
            )
            for code in preparation_codes
        ]

    def _require_outfit_code(self, category: str, code: str) -> None:
        if code not in self.OUTFIT_CATALOG[category]:
            raise InvalidOutfitSelectionError(
                f"{category} 카테고리에서 지원하지 않는 코드입니다: {code}"
            )

    def _sort_and_limit_codes(self, preparation_codes: list[str]) -> list[str]:
        unique_codes = list(dict.fromkeys(preparation_codes))

        return sorted(
            unique_codes,
            key=lambda code: self.PREPARATION_PRIORITY.get(code, 99),
        )[:4]