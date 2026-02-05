"""Technology stack detection from page content."""

import re
from typing import Dict, List, Optional, Any

from proofkit.utils.logger import logger

from .models import SnapshotData, StackInfo


class StackDetector:
    """Detect CMS, frameworks, analytics, and other technologies."""

    # CMS detection patterns (check in HTML content)
    CMS_PATTERNS = {
        "wordpress": [
            r"wp-content/",
            r"wp-includes/",
            r'<meta name="generator" content="WordPress',
            r"wordpress",
        ],
        "shopify": [
            r"cdn\.shopify\.com",
            r"shopify-buy",
            r"Shopify\.theme",
        ],
        "wix": [
            r"wix\.com",
            r"wixstatic\.com",
            r"X-Wix-",
        ],
        "squarespace": [
            r"squarespace\.com",
            r"static\.squarespace\.com",
            r"squarespace-cdn",
        ],
        "webflow": [
            r"webflow\.com",
            r"assets\.website-files\.com",
            r'class="w-',
        ],
        "drupal": [
            r"drupal\.js",
            r"/sites/default/files/",
            r'<meta name="generator" content="Drupal',
        ],
        "joomla": [
            r"/media/jui/",
            r"/components/com_",
            r'<meta name="generator" content="Joomla',
        ],
        "magento": [
            r"mage/cookies\.js",
            r"Magento_",
            r"/static/version",
        ],
        "ghost": [
            r"ghost\.io",
            r'<meta name="generator" content="Ghost',
        ],
        "hubspot": [
            r"hs-scripts\.com",
            r"hubspot\.com",
            r"hbspt\.forms",
        ],
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "react": [
            r"react\.js",
            r"react\.production\.min\.js",
            r"_reactRootContainer",
            r"__NEXT_DATA__",  # Next.js (React)
            r"data-reactroot",
        ],
        "vue": [
            r"vue\.js",
            r"vue\.min\.js",
            r"__vue__",
            r"data-v-",
        ],
        "angular": [
            r"angular\.js",
            r"ng-version",
            r"ng-app",
            r"angular\.min\.js",
        ],
        "jquery": [
            r"jquery\.js",
            r"jquery\.min\.js",
            r"jquery-\d",
        ],
        "bootstrap": [
            r"bootstrap\.css",
            r"bootstrap\.min\.js",
            r'class="[^"]*\b(container|row|col-)',
        ],
        "tailwind": [
            r"tailwind",
            r'class="[^"]*\b(flex|grid|mt-|mb-|px-|py-)',
        ],
        "nextjs": [
            r"__NEXT_DATA__",
            r"_next/static",
        ],
        "nuxt": [
            r"__NUXT__",
            r"_nuxt/",
        ],
        "gatsby": [
            r"gatsby-",
            r"___gatsby",
        ],
        "svelte": [
            r"svelte",
            r"__svelte",
        ],
    }

    # Analytics detection patterns
    ANALYTICS_PATTERNS = {
        "google_analytics": [
            r"google-analytics\.com/analytics\.js",
            r"googletagmanager\.com",
            r"gtag\(",
            r"ga\('send'",
            r"_ga=",
        ],
        "google_analytics_4": [
            r"G-[A-Z0-9]+",
            r"gtag\.js\?id=G-",
        ],
        "facebook_pixel": [
            r"connect\.facebook\.net",
            r"fbq\(",
            r"facebook-pixel",
        ],
        "hotjar": [
            r"hotjar\.com",
            r"hjid",
        ],
        "mixpanel": [
            r"mixpanel\.com",
            r"mixpanel\.init",
        ],
        "segment": [
            r"segment\.com",
            r"analytics\.js",
        ],
        "amplitude": [
            r"amplitude\.com",
            r"amplitude\.init",
        ],
        "clarity": [
            r"clarity\.ms",
            r"microsoft clarity",
        ],
    }

    # Tag manager patterns
    TAG_MANAGER_PATTERNS = {
        "google_tag_manager": [
            r"googletagmanager\.com/gtm\.js",
            r"GTM-[A-Z0-9]+",
        ],
        "tealium": [
            r"tealium\.com",
            r"utag\.js",
        ],
        "adobe_launch": [
            r"adobedtm\.com",
            r"launch\.js",
        ],
    }

    # CDN detection patterns
    CDN_PATTERNS = {
        "cloudflare": [
            r"cdnjs\.cloudflare\.com",
            r"cf-ray",
            r"cloudflare",
        ],
        "fastly": [
            r"fastly",
            r"x-served-by.*cache-",
        ],
        "akamai": [
            r"akamai",
            r"akadns",
        ],
        "cloudfront": [
            r"cloudfront\.net",
            r"x-amz-cf-",
        ],
        "jsdelivr": [
            r"jsdelivr\.net",
        ],
        "unpkg": [
            r"unpkg\.com",
        ],
    }

    # E-commerce platform patterns
    ECOMMERCE_PATTERNS = {
        "woocommerce": [
            r"woocommerce",
            r"wc-cart",
            r"/wc-ajax/",
        ],
        "magento": [
            r"Magento",
            r"mage/",
        ],
        "bigcommerce": [
            r"bigcommerce",
        ],
        "prestashop": [
            r"prestashop",
            r"/modules/ps_",
        ],
        "opencart": [
            r"opencart",
        ],
    }

    def detect(self, snapshot: SnapshotData) -> StackInfo:
        """
        Detect technology stack from snapshot data.

        Args:
            snapshot: SnapshotData from Playwright collector

        Returns:
            StackInfo with detected technologies
        """
        logger.info("Detecting technology stack")

        # Combine HTML content from all pages
        html_content = ""
        for page in snapshot.pages:
            if page.html_content:
                html_content += page.html_content

        # If no HTML content, try to get from meta tags and headings
        if not html_content:
            for page in snapshot.pages:
                html_content += str(page.meta_tags)
                for level, headings in page.headings.items():
                    html_content += " ".join(headings)

        # Get headers if available (from HTTP probe, but not here)
        headers = {}

        return StackInfo(
            cms=self._detect_cms(html_content),
            framework=self._detect_framework(html_content),
            analytics=self._detect_analytics(html_content),
            tag_managers=self._detect_tag_managers(html_content),
            cdn=self._detect_cdn(html_content, headers),
            ecommerce_platform=self._detect_ecommerce(html_content),
            other=self._detect_other(html_content),
        )

    def detect_from_html(self, html: str, headers: Optional[Dict[str, str]] = None) -> StackInfo:
        """
        Detect technology stack from raw HTML.

        Args:
            html: Raw HTML content
            headers: Optional HTTP headers

        Returns:
            StackInfo with detected technologies
        """
        headers = headers or {}

        return StackInfo(
            cms=self._detect_cms(html),
            framework=self._detect_framework(html),
            analytics=self._detect_analytics(html),
            tag_managers=self._detect_tag_managers(html),
            cdn=self._detect_cdn(html, headers),
            ecommerce_platform=self._detect_ecommerce(html),
            other=self._detect_other(html),
        )

    def _detect_cms(self, html: str) -> Optional[str]:
        """Detect CMS from HTML content."""
        for cms, patterns in self.CMS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    return cms
        return None

    def _detect_framework(self, html: str) -> Optional[str]:
        """Detect primary frontend framework."""
        # Check in priority order
        priority_order = ["nextjs", "nuxt", "gatsby", "react", "vue", "angular", "svelte"]

        for framework in priority_order:
            patterns = self.FRAMEWORK_PATTERNS.get(framework, [])
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    return framework

        # Check other frameworks
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            if framework not in priority_order:
                for pattern in patterns:
                    if re.search(pattern, html, re.IGNORECASE):
                        return framework

        return None

    def _detect_analytics(self, html: str) -> List[str]:
        """Detect analytics tools."""
        found = []

        for tool, patterns in self.ANALYTICS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    if tool not in found:
                        found.append(tool)
                    break

        return found

    def _detect_tag_managers(self, html: str) -> List[str]:
        """Detect tag managers."""
        found = []

        for tool, patterns in self.TAG_MANAGER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    if tool not in found:
                        found.append(tool)
                    break

        return found

    def _detect_cdn(self, html: str, headers: Dict[str, str]) -> Optional[str]:
        """Detect CDN from HTML and headers."""
        # Check headers first
        header_str = str(headers).lower()
        for cdn, patterns in self.CDN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, header_str, re.IGNORECASE):
                    return cdn

        # Check HTML
        for cdn, patterns in self.CDN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    return cdn

        return None

    def _detect_ecommerce(self, html: str) -> Optional[str]:
        """Detect e-commerce platform."""
        for platform, patterns in self.ECOMMERCE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    return platform
        return None

    def _detect_other(self, html: str) -> List[str]:
        """Detect other notable technologies."""
        other = []

        # Font libraries
        if re.search(r"fonts\.googleapis\.com", html, re.IGNORECASE):
            other.append("google_fonts")
        if re.search(r"use\.fontawesome\.com|fontawesome", html, re.IGNORECASE):
            other.append("font_awesome")

        # Chat widgets
        if re.search(r"intercom", html, re.IGNORECASE):
            other.append("intercom")
        if re.search(r"drift\.com", html, re.IGNORECASE):
            other.append("drift")
        if re.search(r"crisp\.chat|crisp\.im", html, re.IGNORECASE):
            other.append("crisp")
        if re.search(r"tawk\.to", html, re.IGNORECASE):
            other.append("tawk")
        if re.search(r"zendesk", html, re.IGNORECASE):
            other.append("zendesk")

        # A/B testing
        if re.search(r"optimizely", html, re.IGNORECASE):
            other.append("optimizely")
        if re.search(r"vwo\.com|visualwebsiteoptimizer", html, re.IGNORECASE):
            other.append("vwo")

        # Recaptcha
        if re.search(r"recaptcha|grecaptcha", html, re.IGNORECASE):
            other.append("recaptcha")

        return other
