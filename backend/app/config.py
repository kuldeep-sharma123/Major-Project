"""
Application configuration using Pydantic Settings.
All environment variables are validated and typed here.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "AI Autonomous Testing Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/test_agent.db"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Return async-compatible URL."""
        if self.DATABASE_URL.startswith("sqlite"):
            if not self.DATABASE_URL.startswith("sqlite+aiosqlite"):
                return self.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
            return self.DATABASE_URL
        return self.DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        ).replace("psycopg2://", "postgresql+asyncpg://", 1)

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ── AI Providers ──────────────────────────────────────────────────────────
    AI_PROVIDER: str = "openai"          # "openai" | "gemini"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    AI_TEMPERATURE: float = 0.2
    AI_MAX_TOKENS: int = 4096
    AI_MAX_RETRIES: int = 3

    # ── Storage ───────────────────────────────────────────────────────────────
    STORAGE_PATH: str = "./storage"
    CHROMADB_PATH: str = "./chromadb"

    @property
    def storage_root(self) -> Path:
        path = Path(self.STORAGE_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def screenshots_dir(self) -> Path:
        d = self.storage_root / "screenshots"
        d.mkdir(exist_ok=True)
        return d

    @property
    def videos_dir(self) -> Path:
        d = self.storage_root / "videos"
        d.mkdir(exist_ok=True)
        return d

    @property
    def logs_dir(self) -> Path:
        d = self.storage_root / "logs"
        d.mkdir(exist_ok=True)
        return d

    @property
    def scripts_dir(self) -> Path:
        d = self.storage_root / "scripts"
        d.mkdir(exist_ok=True)
        return d

    @property
    def reports_dir(self) -> Path:
        d = self.storage_root / "reports"
        d.mkdir(exist_ok=True)
        return d

    # Aliases
    @property
    def reports_path(self) -> Path:
        return self.reports_dir

    @property
    def screenshots_path(self) -> Path:
        return self.screenshots_dir

    @property
    def videos_path(self) -> Path:
        return self.videos_dir

    @property
    def logs_path(self) -> Path:
        return self.logs_dir

    @property
    def generated_scripts_path(self) -> Path:
        return self.scripts_dir

    # ── Playwright ────────────────────────────────────────────────────────────
    PLAYWRIGHT_FRAMEWORK_PATH: str = "./playwright_framework"
    HEADLESS: bool = True
    BROWSER_TYPE: str = "chromium"

    # ── Crawler ───────────────────────────────────────────────────────────────
    MAX_CRAWL_PAGES: int = 50
    CRAWL_TIMEOUT_MS: int = 30_000
    CRAWL_RATE_LIMIT_MS: int = 500

    # ── Redis / Celery ────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()


settings: Settings = get_settings()
