"""Tests for stack detector."""

import pytest

from proofkit.collector.stack_detector import StackDetector
from proofkit.collector.models import SnapshotData, PageSnapshot


class TestStackDetector:
    def test_init(self):
        detector = StackDetector()
        assert detector is not None
        assert len(detector.CMS_PATTERNS) > 0
        assert len(detector.FRAMEWORK_PATTERNS) > 0


class TestCMSDetection:
    def test_detect_wordpress(self):
        detector = StackDetector()
        html = """
        <html>
        <head>
            <link rel="stylesheet" href="/wp-content/themes/theme/style.css">
        </head>
        <body>
            <script src="/wp-includes/js/jquery.js"></script>
        </body>
        </html>
        """
        result = detector._detect_cms(html)
        assert result == "wordpress"

    def test_detect_shopify(self):
        detector = StackDetector()
        html = """
        <html>
        <head>
            <link rel="stylesheet" href="//cdn.shopify.com/styles.css">
        </head>
        <body>
            <script>Shopify.theme = {}</script>
        </body>
        </html>
        """
        result = detector._detect_cms(html)
        assert result == "shopify"

    def test_detect_webflow(self):
        detector = StackDetector()
        html = """
        <html>
        <head>
            <link rel="stylesheet" href="https://assets.website-files.com/style.css">
        </head>
        <body class="w-nav">
        </body>
        </html>
        """
        result = detector._detect_cms(html)
        assert result == "webflow"

    def test_no_cms_detected(self):
        detector = StackDetector()
        html = "<html><body><h1>Simple page</h1></body></html>"
        result = detector._detect_cms(html)
        assert result is None


class TestFrameworkDetection:
    def test_detect_react(self):
        detector = StackDetector()
        html = '<div id="root" data-reactroot></div>'
        result = detector._detect_framework(html)
        assert result == "react"

    def test_detect_nextjs(self):
        detector = StackDetector()
        html = '<script id="__NEXT_DATA__" type="application/json">{}</script>'
        result = detector._detect_framework(html)
        assert result == "nextjs"

    def test_detect_vue(self):
        detector = StackDetector()
        html = '<div data-v-abc123></div><script src="vue.min.js"></script>'
        result = detector._detect_framework(html)
        assert result == "vue"

    def test_detect_angular(self):
        detector = StackDetector()
        html = '<app-root ng-version="15.0.0"></app-root>'
        result = detector._detect_framework(html)
        assert result == "angular"

    def test_no_framework_detected(self):
        detector = StackDetector()
        html = "<html><body><h1>Static page</h1></body></html>"
        result = detector._detect_framework(html)
        assert result is None


class TestAnalyticsDetection:
    def test_detect_google_analytics(self):
        detector = StackDetector()
        html = '<script src="https://www.google-analytics.com/analytics.js"></script>'
        result = detector._detect_analytics(html)
        assert "google_analytics" in result

    def test_detect_gtm(self):
        detector = StackDetector()
        html = '<script>gtag("config", "G-ABCD1234")</script>'
        result = detector._detect_analytics(html)
        # Should detect GA4
        assert len(result) > 0

    def test_detect_facebook_pixel(self):
        detector = StackDetector()
        html = '<script src="https://connect.facebook.net/pixel.js"></script><script>fbq("init")</script>'
        result = detector._detect_analytics(html)
        assert "facebook_pixel" in result

    def test_detect_multiple_analytics(self):
        detector = StackDetector()
        html = """
        <script src="https://www.google-analytics.com/analytics.js"></script>
        <script src="https://connect.facebook.net/pixel.js"></script>
        <script>fbq("init")</script>
        <script src="https://static.hotjar.com/c/hotjar.js"></script>
        """
        result = detector._detect_analytics(html)
        assert len(result) >= 2

    def test_no_analytics_detected(self):
        detector = StackDetector()
        html = "<html><body><h1>No analytics</h1></body></html>"
        result = detector._detect_analytics(html)
        assert result == []


class TestTagManagerDetection:
    def test_detect_gtm(self):
        detector = StackDetector()
        html = '<script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABCD123"></script>'
        result = detector._detect_tag_managers(html)
        assert "google_tag_manager" in result

    def test_no_tag_manager(self):
        detector = StackDetector()
        html = "<html><body></body></html>"
        result = detector._detect_tag_managers(html)
        assert result == []


class TestCDNDetection:
    def test_detect_cloudflare(self):
        detector = StackDetector()
        html = '<script src="https://cdnjs.cloudflare.com/libs/jquery.js"></script>'
        result = detector._detect_cdn(html, {})
        assert result == "cloudflare"

    def test_detect_cloudflare_from_headers(self):
        detector = StackDetector()
        headers = {"cf-ray": "abc123", "server": "cloudflare"}
        result = detector._detect_cdn("", headers)
        assert result == "cloudflare"

    def test_no_cdn_detected(self):
        detector = StackDetector()
        html = "<html><body></body></html>"
        result = detector._detect_cdn(html, {})
        assert result is None


class TestEcommerceDetection:
    def test_detect_woocommerce(self):
        detector = StackDetector()
        html = '<div class="woocommerce"><form class="wc-cart"></form></div>'
        result = detector._detect_ecommerce(html)
        assert result == "woocommerce"

    def test_no_ecommerce_detected(self):
        detector = StackDetector()
        html = "<html><body><h1>Blog</h1></body></html>"
        result = detector._detect_ecommerce(html)
        assert result is None


class TestOtherDetection:
    def test_detect_google_fonts(self):
        detector = StackDetector()
        html = '<link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">'
        result = detector._detect_other(html)
        assert "google_fonts" in result

    def test_detect_chat_widgets(self):
        detector = StackDetector()
        html = '<script src="https://widget.intercom.io/widget/abc"></script>'
        result = detector._detect_other(html)
        assert "intercom" in result

    def test_detect_recaptcha(self):
        detector = StackDetector()
        html = '<script src="https://www.google.com/recaptcha/api.js"></script>'
        result = detector._detect_other(html)
        assert "recaptcha" in result


class TestFullDetection:
    def test_detect_from_snapshot(self):
        detector = StackDetector()
        snapshot = SnapshotData(
            url="https://example.com",
            pages=[
                PageSnapshot(
                    url="https://example.com",
                    html_content='<div class="woocommerce"></div><script src="https://www.google-analytics.com/analytics.js"></script>',
                )
            ],
        )
        result = detector.detect(snapshot)
        assert result.ecommerce_platform == "woocommerce"
        assert "google_analytics" in result.analytics

    def test_detect_from_html_directly(self):
        detector = StackDetector()
        html = """
        <html>
        <head>
            <link href="/wp-content/themes/theme/style.css" rel="stylesheet">
        </head>
        <body>
            <div data-reactroot></div>
            <script src="https://www.google-analytics.com/analytics.js"></script>
        </body>
        </html>
        """
        result = detector.detect_from_html(html)
        assert result.cms == "wordpress"
        assert result.framework == "react"
        assert "google_analytics" in result.analytics
