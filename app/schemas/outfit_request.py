from pydantic import BaseModel, Field, field_validator


class CurrentWeatherRequest(BaseModel):
    temperature: float = Field(description="현재 기온")
    humidity: int = Field(ge=0, le=100, description="습도")
    windSpeed: float = Field(ge=0, description="풍속")
    windStatus: str = Field(default="약한 바람", description="바람 상태")
    precipitationAmount: str = Field(default="강수 없음", description="강수량 설명")
    precipitationType: str = Field(default="없음", description="강수 형태")
    precipitationProbability: int = Field(
        default=0,
        ge=0,
        le=100,
        description="강수 확률",
    )
    skyStatus: str = Field(default="맑음", description="하늘 상태")
    weatherCondition: str = Field(default="맑음", description="종합 날씨 상태")


class FeelsLikeWeatherRequest(BaseModel):
    feelsLikeTemperature: float = Field(description="체감온도")
    temperatureDifference: float = Field(
        default=0,
        description="현재 기온과 체감온도 차이",
    )
    description: str = Field(default="", description="체감 날씨 설명")
    factors: list[str] = Field(default_factory=list, description="체감 날씨 요인")


class OutfitRecommendationRequest(BaseModel):
    region: str = Field(min_length=1, max_length=20, description="선택한 충북 지역")
    currentWeather: CurrentWeatherRequest
    feelsLikeWeather: FeelsLikeWeatherRequest
    travelStyle: str = Field(
        min_length=1,
        max_length=30,
        description="여행 스타일",
        examples=["관광", "축제", "레포츠", "자연 탐방"],
    )

    @field_validator("region", "travelStyle")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("빈 문자열은 입력할 수 없습니다.")

        return normalized_value