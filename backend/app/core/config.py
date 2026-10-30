# backend/app/core/config.py
from typing import Optional
from pathlib import Path
from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings

# Resolve root directory containing .env
BASE_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = BASE_DIR / ".env"

class Settings(BaseSettings):
    APP_ENV: str = Field(default="development")
    APP_DEBUG: bool = Field(default=True)
    APP_SECRET_KEY: SecretStr = Field(...)

    DATABASE_URL: str = Field(...)

    JWT_SECRET_KEY: SecretStr = Field(...)
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    GOOGLE_API_KEY: SecretStr = Field(...)
    PLAID_CLIENT_ID: str = Field(...)
    PLAID_SECRET: SecretStr = Field(...)
    PLAID_ENV: str = Field(default="sandbox")

    LOG_LEVEL: str = Field(default="INFO")

    OPENAI_API_KEY: Optional[SecretStr] = Field(default=None)
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash")

    model_config = {
        "env_file": str(ENV_PATH) if ENV_PATH.exists() else ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        missing_fields = []
        for err in exc.errors():
            loc = err.get("loc", ())
            if loc:
                missing_fields.append(str(loc[0]))
        msg = f"Missing or invalid required environment variable(s): {', '.join(missing_fields)}"
        raise RuntimeError(msg) from None


settings = load_settings()
