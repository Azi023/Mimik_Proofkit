"""Tests for finding deduplication and business impact scoring."""

import pytest
from proofkit.schemas.finding import Finding, Severity, Effort, Category, Evidence
from proofkit.analyzer.deduplication import deduplicate_findings, deduplicate_with_stats, FindingDeduplicator
from proofkit.analyzer.impact_scorer import score_by_business_impact, BusinessImpactScorer, ImpactCategory


def create_finding(
    id: str,
    title: str,
    category: str = "CONVERSION",
    severity: str = "P2",
    summary: str = "Test summary",
    impact: str = "Test impact",
    url: str = "https://example.com",
) -> Finding:
    """Helper to create test findings."""
    return Finding(
        id=id,
        title=title,
        category=Category(category),
        severity=Severity(severity),
        summary=summary,
        impact=impact,
        recommendation="Test recommendation",
        effort=Effort.M,
        evidence=[Evidence(url=url)] if url else [],
        tags=[],
        confidence=1.0,
    )


class TestFindingDeduplication:
    """Test the FindingDeduplicator class."""

    def test_no_duplicates(self):
        """Test with unique findings - no deduplication needed."""
        findings = [
            create_finding("UX-001", "Missing navigation"),
            create_finding("SEO-001", "Missing meta description"),
            create_finding("CONV-001", "No CTA on homepage"),
        ]

        result = deduplicate_findings(findings)
        assert len(result) == 3

    def test_exact_duplicates_merge(self):
        """Test that exact duplicates are merged."""
        findings = [
            create_finding("CONV-BTN-001", "Weak form button text: 'Submit'", url="https://example.com/page1"),
            create_finding("CONV-BTN-001", "Weak form button text: 'Submit'", url="https://example.com/page2"),
            create_finding("CONV-BTN-001", "Weak form button text: 'Submit'", url="https://example.com/page3"),
            create_finding("CONV-BTN-001", "Weak form button text: 'Submit'", url="https://example.com/page4"),
            create_finding("CONV-BTN-001", "Weak form button text: 'Submit'", url="https://example.com/page5"),
            create_finding("CONV-BTN-001", "Weak form button text: 'Submit'", url="https://example.com/page6"),
        ]

        result = deduplicate_findings(findings)

        # All 6 should be merged into 1
        assert len(result) == 1
        # Title should mention occurrence count
        assert "6 occurrences" in result[0].title or "occurrences" in result[0].summary

    def test_similar_titles_merge(self):
        """Test that similar titles (>80% match) are merged."""
        findings = [
            create_finding("UX-001", "Missing navigation menu on homepage"),
            create_finding("UX-002", "Missing navigation menu on contact page"),
            create_finding("UX-003", "Missing navigation menu on about page"),
        ]

        result = deduplicate_findings(findings)

        # Similar titles should be deduplicated
        assert len(result) < 3

    def test_identical_titles_merged_across_categories(self):
        """Test that findings with identical titles are merged even across categories.

        This is the desired behavior - if the same issue appears in both UX and
        CONVERSION categories, it's essentially the same problem and should be
        reported once to reduce noise.
        """
        findings = [
            create_finding("UX-001", "No call-to-action button", category="UX"),
            create_finding("CONV-001", "No call-to-action button", category="CONVERSION"),
        ]

        # These have identical titles and should be merged by similarity deduplication
        result = deduplicate_findings(findings)
        assert len(result) == 1  # Merged into one finding

    def test_severity_preserved_on_merge(self):
        """Test that highest severity is preserved when merging duplicates."""
        findings = [
            create_finding("CONV-001", "Missing CTA", severity="P3"),
            create_finding("CONV-001", "Missing CTA", severity="P0"),  # Highest
            create_finding("CONV-001", "Missing CTA", severity="P2"),
        ]

        result = deduplicate_findings(findings)

        assert len(result) == 1
        severity = result[0].severity
        sev_val = severity.value if hasattr(severity, 'value') else severity
        assert sev_val == "P0"  # Should keep P0 (highest)

    def test_stats_tracking(self):
        """Test that deduplication statistics are tracked correctly."""
        findings = [
            create_finding("A-001", "Finding A"),
            create_finding("A-001", "Finding A"),
            create_finding("B-001", "Finding B"),
            create_finding("B-001", "Finding B"),
            create_finding("B-001", "Finding B"),
            create_finding("C-001", "Finding C"),
        ]

        result, stats = deduplicate_with_stats(findings)

        assert stats["original_count"] == 6
        assert stats["duplicates_merged"] > 0


class TestBusinessImpactScorer:
    """Test the BusinessImpactScorer class."""

    def test_revenue_keywords_boost_score(self):
        """Test that revenue-related keywords boost the impact score."""
        finding_with_cta = create_finding(
            "CONV-001",
            "Missing CTA button on checkout page",
            summary="The checkout form has no clear conversion button",
        )
        finding_basic = create_finding(
            "TECH-001",
            "Missing console log",
            summary="Console has deprecation warning",
        )

        scored = score_by_business_impact([finding_with_cta, finding_basic])

        # CTA/checkout finding should rank higher
        assert scored[0].finding.id == "CONV-001"
        assert scored[0].impact_category == ImpactCategory.REVENUE

    def test_trust_keywords_categorization(self):
        """Test that security keywords are categorized as trust."""
        finding = create_finding(
            "SEC-001",
            "Missing SSL certificate",
            summary="Site not served over HTTPS, security risk",
        )

        scored = score_by_business_impact([finding])

        assert scored[0].impact_category == ImpactCategory.TRUST

    def test_severity_multiplier(self):
        """Test that higher severity findings get higher scores."""
        critical = create_finding("A-001", "Test finding", severity="P0")
        low = create_finding("B-001", "Test finding", severity="P3")

        scored = score_by_business_impact([critical, low])

        # P0 should score higher than P3
        p0_score = next(s for s in scored if s.finding.id == "A-001")
        p3_score = next(s for s in scored if s.finding.id == "B-001")

        assert p0_score.impact_score > p3_score.impact_score

    def test_business_type_adjustment(self):
        """Test that business type affects scoring keywords."""
        finding = create_finding(
            "CONV-001",
            "No property viewing form",
            summary="Users cannot schedule property viewings",
        )

        # Score with real_estate business type
        scored_re = score_by_business_impact([finding], "real_estate")

        # Score without business type
        scored_generic = score_by_business_impact([finding], None)

        # Real estate should score higher due to 'property', 'viewing' keywords
        assert scored_re[0].impact_score >= scored_generic[0].impact_score

    def test_priority_ranking(self):
        """Test that findings are ranked by impact score."""
        findings = [
            create_finding("LOW-001", "Minor styling issue", category="UX"),
            create_finding("HIGH-001", "Checkout form broken", category="CONVERSION", severity="P0"),
            create_finding("MED-001", "Page loads slowly", category="PERFORMANCE"),
        ]

        scored = score_by_business_impact(findings)

        # Check ranking is assigned
        for i, sf in enumerate(scored):
            assert sf.priority_rank == i + 1


class TestIntegration:
    """Integration tests for the full deduplication + scoring pipeline."""

    def test_full_pipeline(self):
        """Test the complete deduplication and scoring pipeline."""
        # Simulate the Seven Tides scenario with many duplicates
        findings = []

        # 6 duplicates of the same form button issue
        for i in range(6):
            findings.append(create_finding(
                f"CONV-BTN-001",
                "Weak form button text: 'Submit'",
                url=f"https://example.com/page{i}",
            ))

        # Multiple pages with missing CTAs
        for i in range(22):
            findings.append(create_finding(
                f"CONV-CTA-001",
                "Page lacks clear CTA",
                url=f"https://example.com/page{i}",
            ))

        # Various other findings
        findings.append(create_finding("SEO-001", "Missing meta description"))
        findings.append(create_finding("SEC-001", "Missing security headers"))
        findings.append(create_finding("UX-001", "No navigation menu"))

        original_count = len(findings)
        assert original_count == 31  # 6 + 22 + 3

        # Deduplicate
        deduplicated, stats = deduplicate_with_stats(findings)

        # Should be significantly reduced
        assert len(deduplicated) < original_count
        assert stats["duplicates_merged"] > 0

        # Score by business impact
        scored = score_by_business_impact(deduplicated)

        # All should have rankings
        assert all(sf.priority_rank > 0 for sf in scored)

        # Scores should be sorted descending
        for i in range(len(scored) - 1):
            assert scored[i].impact_score >= scored[i + 1].impact_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
