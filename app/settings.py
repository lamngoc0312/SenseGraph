"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DIAGRAM_SCHEMA_PATH = CONTRACTS_DIR / "diagram.schema.json"

SUPPORTED_DOMAINS: tuple[str, ...] = ("physics_circuit", "biology_food_web")


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings."""

    ai_provider: str = "none"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    ai_timeout_seconds: float = 30.0
    max_upload_mb: int = 5
    fixtures_dir: Path = FIXTURES_DIR
    schema_path: Path = DIAGRAM_SCHEMA_PATH

    @property
    def ai_configured(self) -> bool:
        """Return True only when a supported AI provider has credentials configured."""
        return self.ai_provider.strip().lower() == "gemini" and bool(
            self.gemini_api_key.strip()
        )


def load_settings() -> Settings:
    """Load settings from .env (if present) and process environment."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    ai_provider = os.getenv("AI_PROVIDER", "none").strip().lower() or "none"
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

    raw_timeout = os.getenv("AI_TIMEOUT_SECONDS", "30").strip()
    try:
        ai_timeout_seconds = max(5.0, float(raw_timeout))
    except ValueError:
        ai_timeout_seconds = 30.0

    raw_max_mb = os.getenv("MAX_UPLOAD_MB", "5").strip()
    try:
        max_upload_mb = max(1, int(raw_max_mb))
    except ValueError:
        max_upload_mb = 5

    return Settings(
        ai_provider=ai_provider,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        ai_timeout_seconds=ai_timeout_seconds,
        max_upload_mb=max_upload_mb,
    )
