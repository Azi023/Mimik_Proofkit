"""Shared pytest fixtures for ProofKit tests."""

import pytest
from pathlib import Path
import tempfile
import os


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.setenv("PROOFKIT_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("PROOFKIT_OUTPUT_DIR", "/tmp/proofkit_test")


@pytest.fixture
def sample_url():
    """Return a sample URL for testing."""
    return "https://example.com"
