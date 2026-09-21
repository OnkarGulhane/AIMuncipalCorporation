from typing import List, Union, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Case Manager"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    ENABLE_DOCS: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./ai_case_manager.db"

    # Security
    JWT_SECRET_KEY: str = "development_jwt_secret_key_minimum_32_characters_long_12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    SECURE_COOKIES: bool = False

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # AI Service Settings
    AI_PROVIDER: str = "gemini"
    AI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    AI_API_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"

    # Storage Settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 15
    STORAGE_BUCKET_NAME: str = "case-evidence"
    STORAGE_ENDPOINT_URL: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""

    # Email / SMTP Settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    EMAILS_FROM_EMAIL: str = "notifications@city.gov"
    EMAILS_FROM_NAME: str = "AI Municipal Corporation"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @model_validator(mode="after")
    def validate_production_guards(self) -> "Settings":
        if self.is_production:
            if "development_jwt_secret_key" in self.JWT_SECRET_KEY:
                raise ValueError("Production requires a strong, randomly generated JWT_SECRET_KEY (not the default development key).")
            if len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("Production JWT_SECRET_KEY must be at least 32 characters long.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
