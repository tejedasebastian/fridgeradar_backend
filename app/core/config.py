from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Fridge Inventory API"

    # Sin valores por defecto: la app falla al arrancar si no se configuran
    # por entorno (o en un `.env` local, que está git-ignored).
    database_url: str
    jwt_secret: str = Field(min_length=32)

    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7
    environment: str = "local"
    gemini_api_key: str = ""

    # Orígenes permitidos por CORS, separados por coma. Configurable por
    # entorno para no quedar atado a localhost en staging/producción.
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001"
    )

    # Gemini model selection. Some free-tier keys don't have access to
    # `gemini-2.0-flash` (returns 422). If the primary model returns 422
    # the service falls back to `gemini_fallback_model`. If both fail, the
    # request returns FALLBACK_RECIPES (for /api/recipes/suggest) or 503
    # (for /api/ai/chat).
    gemini_model: str = "gemini-2.0-flash"
    gemini_fallback_model: str = "gemini-1.5-flash"

    # Gemini throttle tunables. Default values match the free-tier quotas
    # (15 RPM, 1500 RPD). Override in `.env` for development or for paid
    # keys with higher limits.
    gemini_min_interval_s: float = 4.0          # min seconds between calls
    gemini_cooldown_base_s: float = 60.0        # first 429 -> 60s cooldown
    gemini_cooldown_max_s: float = 3600.0        # cap exponential backoff at 1h
    gemini_cache_ttl_s: float = 300.0           # success -> cache 5 min
    gemini_cache_neg_ttl_s: float = 30.0        # failure -> cache 30s

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
