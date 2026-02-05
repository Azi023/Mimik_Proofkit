"""Configuration management for ProofKit."""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, Dict
from pathlib import Path


class ProofKitSettings(BaseSettings):
    """ProofKit configuration loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Paths
    output_dir: Path = Field(default=Path("./runs"), alias="PROOFKIT_OUTPUT_DIR")
    templates_dir: Path = Field(default=Path("./templates"), alias="PROOFKIT_TEMPLATES_DIR")

    # Collector settings
    playwright_timeout: int = Field(default=60000, alias="PROOFKIT_PLAYWRIGHT_TIMEOUT")
    lighthouse_throttling: str = Field(default="mobile", alias="PROOFKIT_LIGHTHOUSE_THROTTLING")
    max_pages_fast: int = Field(default=5, alias="PROOFKIT_MAX_PAGES_FAST")
    max_pages_full: int = Field(default=50, alias="PROOFKIT_MAX_PAGES_FULL")

    # Analyzer settings
    score_weights: Dict[str, float] = Field(default={
        "PERFORMANCE": 0.25,
        "SEO": 0.20,
        "CONVERSION": 0.25,
        "UX": 0.15,
        "SECURITY": 0.10,
        "MAINTENANCE": 0.05,
    })

    # Narrator settings
    ai_model: str = Field(default="claude-sonnet-4-20250514", alias="PROOFKIT_AI_MODEL")
    ai_max_tokens: int = Field(default=2000, alias="PROOFKIT_AI_MAX_TOKENS")

    # Logging
    log_level: str = Field(default="INFO", alias="PROOFKIT_LOG_LEVEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }


# Singleton config instance
_config: Optional[ProofKitSettings] = None


def get_config() -> ProofKitSettings:
    """Get the singleton configuration instance."""
    global _config
    if _config is None:
        _config = ProofKitSettings()
    return _config


def reset_config() -> None:
    """Reset the singleton configuration (useful for testing)."""
    global _config
    _config = None
