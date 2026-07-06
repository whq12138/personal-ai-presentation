"""
Application configuration — Phase 3: Multi-tenant SaaS with auth, DB, async queue.
"""

import os
from functools import lru_cache


class Settings:
    # ============================================================
    # Server
    # ============================================================
    APP_NAME: str = "Personal AI Presentation API"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # ============================================================
    # Database (SQLite for dev, Postgres-compatible schema)
    # ============================================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./data.db",
    )

    # ============================================================
    # JWT Authentication
    # ============================================================
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production-use-random-64-char")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    JWT_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

    # ============================================================
    # LLM — Multi-Provider Routing
    # ============================================================
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", os.getenv("OPENAI_MODEL", "gpt-4o"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    @property
    def OPENAI_API_KEY(self) -> str: return self.LLM_API_KEY
    @property
    def OPENAI_MODEL(self) -> str: return self.LLM_MODEL_NAME

    # ============================================================
    # Image Generation
    # ============================================================
    IMAGE_PROVIDER: str = os.getenv("IMAGE_PROVIDER", "none")
    IMAGE_API_ENDPOINT: str = os.getenv("IMAGE_API_ENDPOINT", "")
    IMAGE_API_KEY: str = os.getenv("IMAGE_API_KEY", "")
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "dall-e-3")
    IMAGE_DEFAULT_WIDTH: int = int(os.getenv("IMAGE_DEFAULT_WIDTH", "1280"))
    IMAGE_DEFAULT_HEIGHT: int = int(os.getenv("IMAGE_DEFAULT_HEIGHT", "720"))

    # ============================================================
    # Rate Limiting & User Tiers (Phase 3)
    # ============================================================
    RATE_LIMIT_BACKEND: str = os.getenv("RATE_LIMIT_BACKEND", "memory")  # "memory" | "redis"
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Free tier limits
    FREE_GENERATIONS_PER_HOUR: int = int(os.getenv("FREE_GENERATIONS_PER_HOUR", "3"))
    FREE_GENERATIONS_PER_DAY: int = int(os.getenv("FREE_GENERATIONS_PER_DAY", "10"))
    FREE_EXPORT_PER_HOUR: int = int(os.getenv("FREE_EXPORT_PER_HOUR", "5"))
    # Premium tier limits
    PREMIUM_GENERATIONS_PER_HOUR: int = int(os.getenv("PREMIUM_GENERATIONS_PER_HOUR", "60"))
    PREMIUM_GENERATIONS_PER_DAY: int = int(os.getenv("PREMIUM_GENERATIONS_PER_DAY", "480"))

    # Layout tiers — delegated to LayoutRegistry (backend/app/layouts/plugins.py)
    # Free users get all non-premium plugins; Premium users get everything.
    # Adding a new layout plugin → just add one class in plugins.py.
    # No changes needed here.
    @property
    def FREE_LAYOUTS(self) -> list[str]:
        from app.layouts.registry import layout_registry
        return layout_registry.get_names(tier="free")

    @property
    def PREMIUM_LAYOUTS(self) -> list[str]:
        from app.layouts.registry import layout_registry
        return layout_registry.get_names(tier="premium")

    # ============================================================
    # Payment (Phase 3 Step 4)
    # ============================================================
    PAYMENT_WEBHOOK_SECRET: str = os.getenv("PAYMENT_WEBHOOK_SECRET", "dev-secret-change-me")
    PAYMENT_MERCHANT_ID: str = os.getenv("PAYMENT_MERCHANT_ID", "")
    PAYMENT_GATEWAY_URL: str = os.getenv("PAYMENT_GATEWAY_URL", "")
    PAYMENT_RETURN_URL: str = os.getenv("PAYMENT_RETURN_URL", "http://localhost:3000")
    PAYMENT_SANDBOX_MODE: bool = os.getenv("PAYMENT_SANDBOX_MODE", "true").lower() == "true"

    # ============================================================
    # Async Task Queue
    # ============================================================
    MAX_CONCURRENT_TASKS: int = int(os.getenv("MAX_CONCURRENT_TASKS", "4"))
    TASK_TIMEOUT_SECONDS: int = int(os.getenv("TASK_TIMEOUT_SECONDS", "300"))
    TASK_CLEANUP_HOURS: int = int(os.getenv("TASK_CLEANUP_HOURS", "1"))

    # ============================================================
    # Data Privacy — Auto-purge
    # ============================================================
    AUTO_PURGE_HOURS: int = int(os.getenv("AUTO_PURGE_HOURS", "24"))

    # ============================================================
    # File Upload
    # ============================================================
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))


@lru_cache()
def get_settings() -> Settings:
    return Settings()
