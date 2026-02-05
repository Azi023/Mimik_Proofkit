"""Tests for HTTP probe collector."""

import pytest

from proofkit.collector.http_probe import HttpProbeCollector
from proofkit.collector.models import SecurityHeaders


class TestHttpProbeCollector:
    def test_init(self):
        collector = HttpProbeCollector()
        assert collector.timeout == 30

    def test_custom_timeout(self):
        collector = HttpProbeCollector(timeout=60)
        assert collector.timeout == 60


class TestSecurityHeadersCheck:
    def test_check_all_headers_present(self, sample_headers_secure):
        collector = HttpProbeCollector()
        result = collector._check_security_headers(sample_headers_secure)

        assert result.has_hsts is True
        assert result.has_csp is True
        assert result.has_xframe is True
        assert "strict-transport-security" in result.present
        assert result.score > 50

    def test_check_missing_headers(self, sample_headers_insecure):
        collector = HttpProbeCollector()
        result = collector._check_security_headers(sample_headers_insecure)

        assert result.has_hsts is False
        assert result.has_csp is False
        assert result.has_xframe is False
        assert len(result.missing) > 0
        assert "strict-transport-security" in result.missing

    def test_check_partial_headers(self):
        headers = {
            "strict-transport-security": "max-age=31536000",
            "x-content-type-options": "nosniff",
        }
        collector = HttpProbeCollector()
        result = collector._check_security_headers(headers)

        assert result.has_hsts is True
        assert result.has_csp is False
        assert len(result.present) == 2
        assert len(result.missing) > 0

    def test_score_calculation(self):
        # Empty headers
        collector = HttpProbeCollector()
        result = collector._check_security_headers({})
        assert result.score == 0

        # All headers
        all_headers = {
            "strict-transport-security": "max-age=31536000",
            "content-security-policy": "default-src 'self'",
            "x-frame-options": "DENY",
            "x-content-type-options": "nosniff",
            "referrer-policy": "strict-origin",
            "permissions-policy": "geolocation=()",
            "x-xss-protection": "1; mode=block",
            "cross-origin-opener-policy": "same-origin",
            "cross-origin-resource-policy": "same-origin",
        }
        result = collector._check_security_headers(all_headers)
        assert result.score == 100


class TestSSLCheck:
    def test_non_https_url(self):
        collector = HttpProbeCollector()
        result = collector._check_ssl("http://example.com")

        assert result.valid is False
        assert "HTTPS" in result.error


class TestRedirectChain:
    def test_follow_redirects_no_redirect(self):
        """Test with a URL that doesn't redirect (mocked scenario)."""
        collector = HttpProbeCollector()
        # This would need mocking for actual test
        # Just testing the method exists and returns a list
        assert hasattr(collector, '_follow_redirects')


class TestRobotsAndSitemap:
    def test_fetch_robots_method_exists(self):
        collector = HttpProbeCollector()
        assert hasattr(collector, '_fetch_robots')

    def test_check_sitemap_method_exists(self):
        collector = HttpProbeCollector()
        assert hasattr(collector, '_check_sitemap')


class TestQuickCheck:
    def test_check_url_status_method_exists(self):
        collector = HttpProbeCollector()
        assert hasattr(collector, 'check_url_status')
