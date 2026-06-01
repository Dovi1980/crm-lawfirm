from typing import List
from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Base Configurations
    PROJECT_NAME: str = "CRM Law Firm MVP"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Rate Limiting
    ENABLE_RATE_LIMITER: bool = True

    # Database
    DATABASE_URL: str

    # JWT Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS settings (e.g. "http://localhost:3000,http://localhost:5173")
    ALLOWED_ORIGINS: str = "http://localhost,http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    # Mail Server Configuration (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@crm-lawfirm.com"

    # Initial Admin Seeding
    FIRST_ADMIN_EMAIL: EmailStr = "admin@estudio.com"
    FIRST_ADMIN_PASSWORD: str = "AdminLawFirm2026!"

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
