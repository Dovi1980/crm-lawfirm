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

    # Cookie Security (refresh token transport)
    # Set COOKIE_SECURE=True in production behind HTTPS. False for local HTTP dev.
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"  # "strict" | "lax" | "none"
    COOKIE_DOMAIN: str = ""  # empty = host-only cookie

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

    # AI provider — universal layer so each firm can plug in whichever model
    # they already pay for. Switching is a config change, not a code change.
    AI_PROVIDER: str = "anthropic"  # anthropic | openai | gemini
    AI_MODEL_DEFAULT: str = "claude-sonnet-4-6"  # default model id passed to the provider
    AI_MODEL_DEEP: str = ""  # optional override for heavy tasks (long drafts)
    AI_ENABLED: bool = True  # global kill switch

    # Provider credentials (only the one for the active provider is required)
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""  # leave empty for default; set for Azure OpenAI / self-hosted
    GEMINI_API_KEY: str = ""

    # File uploads (scanned documentation attached to cases)
    UPLOAD_DIR: str = "/data/attachments"  # mounted Docker volume
    MAX_UPLOAD_MB: int = 15  # per-file cap (kept under Gemini inline_data limit)
    ALLOWED_UPLOAD_MIME: str = (
        "application/pdf,image/png,image/jpeg,image/jpg,image/webp"
    )

    @property
    def allowed_upload_mime(self) -> List[str]:
        return [m.strip() for m in self.ALLOWED_UPLOAD_MIME.split(",") if m.strip()]

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
