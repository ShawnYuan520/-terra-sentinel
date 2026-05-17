import warnings
from pydantic_settings import BaseSettings
from functools import lru_cache

_DEFAULT_SECRET = "change-me-in-production-use-openssl-rand-hex-32"


class Settings(BaseSettings):
    APP_NAME: str = "AgriSpatial AI"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./agrispatial.db"

    # JWT
    SECRET_KEY: str = _DEFAULT_SECRET
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # GEE
    GEE_PROJECT: str = ""
    GEE_SERVICE_ACCOUNT: str = ""
    GEE_KEY_FILE: str = ""
    GEE_PROXY: str = ""  # 国内访问Google需要代理，如 http://127.0.0.1:7890

    # Weather API
    OPENWEATHER_API_KEY: str = ""

    # Raster data (30m WGS84 GeoTIFFs) — 文件不存在时自动降级到合成数据
    RASTER_DATA_DIR: str = "./demo_data"

    # AI — DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:5174"]

    model_config = {"env_file": ".env", "case_sensitive": True}


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.SECRET_KEY == _DEFAULT_SECRET:
        warnings.warn(
            "SECRET_KEY is using the default value! Set SECRET_KEY in .env for production.",
            stacklevel=2,
        )
    return s