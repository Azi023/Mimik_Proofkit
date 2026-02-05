"""Tests for the token manager."""

import pytest

from proofkit.narrator.token_manager import TokenManager
from proofkit.utils.exceptions import TokenLimitError


class TestTokenManager:
    def test_initialization(self):
        """Test token manager initializes with correct defaults."""
        manager = TokenManager()
        assert manager.monthly_budget == 15.0
        assert manager.monthly_usage["input_tokens"] == 0
        assert manager.monthly_usage["output_tokens"] == 0

    def test_custom_budget(self):
        """Test token manager with custom budget."""
        manager = TokenManager(monthly_budget=25.0)
        assert manager.monthly_budget == 25.0

    def test_estimate_usage_basic(self, sample_findings):
        """Test basic usage estimation."""
        manager = TokenManager()
        estimate = manager.estimate_usage(sample_findings, generate_concept=False)

        # Should include input estimate + 3 section outputs
        expected_output = (
            manager.SECTION_ESTIMATES["executive_summary"] +
            manager.SECTION_ESTIMATES["quick_wins"] +
            manager.SECTION_ESTIMATES["strategic_priorities"]
        )
        assert estimate >= expected_output

    def test_estimate_usage_with_concept(self, sample_findings):
        """Test usage estimation with concept generation."""
        manager = TokenManager()
        without_concept = manager.estimate_usage(sample_findings, generate_concept=False)
        with_concept = manager.estimate_usage(sample_findings, generate_concept=True)

        # With concept should be higher
        assert with_concept > without_concept

        # Should include concept sections
        concept_extra = (
            manager.SECTION_ESTIMATES["concept_bullets"] +
            manager.SECTION_ESTIMATES["lovable_prompt"]
        )
        assert with_concept >= without_concept + concept_extra

    def test_check_budget_passes(self, sample_findings):
        """Test budget check passes when within budget."""
        manager = TokenManager(monthly_budget=15.0)

        # Should not raise
        manager.check_budget(1000)

    def test_check_budget_fails(self):
        """Test budget check fails when over budget."""
        manager = TokenManager(monthly_budget=0.01)

        with pytest.raises(TokenLimitError) as exc:
            manager.check_budget(100000)

        assert "exceeds remaining budget" in str(exc.value)

    def test_record_usage(self):
        """Test recording token usage."""
        manager = TokenManager()

        manager.record_usage({"input_tokens": 100, "output_tokens": 200})
        assert manager.monthly_usage["input_tokens"] == 100
        assert manager.monthly_usage["output_tokens"] == 200

        manager.record_usage({"input_tokens": 50, "output_tokens": 100})
        assert manager.monthly_usage["input_tokens"] == 150
        assert manager.monthly_usage["output_tokens"] == 300

    def test_get_usage_report(self):
        """Test getting usage report."""
        manager = TokenManager(monthly_budget=15.0)
        manager.record_usage({"input_tokens": 1000, "output_tokens": 500})

        report = manager.get_usage_report()

        assert report["input_tokens"] == 1000
        assert report["output_tokens"] == 500
        assert report["total_tokens"] == 1500
        assert "estimated_cost" in report
        assert "remaining_budget" in report
        assert "budget_used_percent" in report
        assert report["remaining_budget"] < 15.0

    def test_reset_usage(self):
        """Test resetting usage counters."""
        manager = TokenManager()
        manager.record_usage({"input_tokens": 1000, "output_tokens": 500})

        manager.reset_usage()

        assert manager.monthly_usage["input_tokens"] == 0
        assert manager.monthly_usage["output_tokens"] == 0

    def test_cost_estimation(self):
        """Test cost estimation logic."""
        manager = TokenManager()

        # 2000 tokens, split 50/50
        cost = manager._estimate_cost(2000)

        # 1000 input at $0.003/1K = $0.003
        # 1000 output at $0.015/1K = $0.015
        # Total = $0.018
        assert abs(cost - 0.018) < 0.001

    def test_remaining_budget_calculation(self):
        """Test remaining budget calculation."""
        manager = TokenManager(monthly_budget=15.0)

        initial_remaining = manager._get_remaining_budget()
        assert initial_remaining == 15.0

        # Record some usage
        manager.record_usage({"input_tokens": 10000, "output_tokens": 5000})

        remaining = manager._get_remaining_budget()
        assert remaining < 15.0
        assert remaining > 0
