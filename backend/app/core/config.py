from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # app settings
    APP_NAME: str = "BlockScope Backend"
    DEBUG: bool = False

    # database
    DATABASE_URL: str

    # security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # redis (for caching later)
    REDIS_URL: Optional[str] = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()