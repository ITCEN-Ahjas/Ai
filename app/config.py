from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    weather_api_key: str = ""
    tour_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()