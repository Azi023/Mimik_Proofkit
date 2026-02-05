"""Tests for ProofKit configuration."""

import pytest
import os
from pathlib import Path

from proofkit.utils.config import (
    ProofKitSettings,
    get_config,
    reset_config,
)


class TestProofKitSettings:
    def test_default_settings(self, monkeypatch):
        """Test default configuration values."""
        # Set required env var
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

        settings = ProofKitSettings()

        assert settings.anthropic_api_key == "sk-ant-test-key"
        assert settings.output_dir == Path("./runs")
        assert settings.playwright_timeout == 60000
        assert settings.lighthouse_throttling == "mobile"
        assert settings.max_pages_fast == 5
        assert settings.max_pages_full == 50
        assert settings.ai_model == "claude-sonnet-4-20250514"
        assert settings.ai_max_tokens == 2000
        assert settings.log_level == "INFO"

    def test_custom_settings(self, monkeypatch):
        """Test custom configuration from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-custom-key")
        monkeypatch.setenv("PROOFKIT_OUTPUT_DIR", "/custom/output")
        monkeypatch.setenv("PROOFKIT_PLAYWRIGHT_TIMEOUT", "90000")
        monkeypatch.setenv("PROOFKIT_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("PROOFKIT_MAX_PAGES_FAST", "10")

        settings = ProofKitSettings()

        assert settings.anthropic_api_key == "sk-ant-custom-key"
        assert settings.output_dir == Path("/custom/output")
        assert settings.playwright_timeout == 90000
        assert settings.log_level == "DEBUG"
        assert settings.max_pages_fast == 10

    def test_score_weights(self, monkeypatch):
        """Test default score weights."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

        settings = ProofKitSettings()

        assert settings.score_weights["PERFORMANCE"] == 0.25
        assert settings.score_weights["SEO"] == 0.20
        assert settings.score_weights["CONVERSION"] == 0.25
        assert settings.score_weights["UX"] == 0.15
        assert settings.score_weights["SECURITY"] == 0.10
        assert settings.score_weights["MAINTENANCE"] == 0.05

        # Total should be close to 1.0
        total = sum(settings.score_weights.values())
        assert 0.99 <= total <= 1.01


class TestGetConfig:
    def test_singleton_pattern(self, monkeypatch):
        """Test that get_config returns the same instance."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        reset_config()

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_reset_config(self, monkeypatch):
        """Test that reset_config clears the singleton."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        reset_config()

        config1 = get_config()
        reset_config()
        config2 = get_config()

        # After reset, should be a new instance
        # (same values but different object)
        assert config1 is not config2


class TestConfigPaths:
    def test_output_dir_path_type(self, monkeypatch):
        """Test that output_dir is a Path object."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        monkeypatch.setenv("PROOFKIT_OUTPUT_DIR", "./custom/runs")

        settings = ProofKitSettings()

        assert isinstance(settings.output_dir, Path)
        assert str(settings.output_dir) == "custom/runs"

    def test_templates_dir_path_type(self, monkeypatch):
        """Test that templates_dir is a Path object."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        monkeypatch.setenv("PROOFKIT_TEMPLATES_DIR", "./custom/templates")

        settings = ProofKitSettings()

        assert isinstance(settings.templates_dir, Path)


class TestConfigValidation:
    def test_empty_api_key_allowed(self, monkeypatch):
        """Test that empty API key is allowed (will fail at runtime)."""
        # Clear the env var
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        settings = ProofKitSettings()
        assert settings.anthropic_api_key == ""

    def test_numeric_string_conversion(self, monkeypatch):
        """Test that numeric env vars are converted properly."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        monkeypatch.setenv("PROOFKIT_PLAYWRIGHT_TIMEOUT", "120000")
        monkeypatch.setenv("PROOFKIT_AI_MAX_TOKENS", "4000")

        settings = ProofKitSettings()

        assert settings.playwright_timeout == 120000
        assert isinstance(settings.playwright_timeout, int)
        assert settings.ai_max_tokens == 4000
        assert isinstance(settings.ai_max_tokens, int)
