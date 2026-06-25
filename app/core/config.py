from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Fridge Inventory API"
    database_url: str = "postgresql+psycopg://postgres:CHANGE_ME@localhost:5432/fridge_inventory"
    jwt_secret: str = "CHANGE_ME_GENERATE_A_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7
    environment: str = "local"
    gemini_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
