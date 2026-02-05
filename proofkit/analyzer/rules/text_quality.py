"""
Text Quality Rules - Analyze typography and content readability.

Detects:
- Title and heading quality issues
- CTA text effectiveness
- Content length problems
- Readability concerns
"""

from typing import List

from proofkit.schemas.finding import Finding, Severity, Category, Effort
from .base import BaseRule


class TextQualityRules(BaseRule):
    """
    Analyze text content quality and effectiveness.

    Checks titles, headings, CTAs, and other text content for
    SEO and conversion optimization issues.
    """

    category = Category.UX

    def run(self) -> List[Finding]:
        """Run text quality analysis."""
        for page in self.raw_data.snapshot.pages:
            self._check_title_quality(page)
            self._check_heading_quality(page)
            self._check_cta_text_quality(page)
            self._check_meta_description(page)

        return self.findings

    def _check_title_quality(self, page):
        """Check page title quality."""
        title = page.title

        if not title:
            self.add_finding(
                id="TEXT-TITLE-001",
                severity=Severity.P0,
                title="Missing page title",
                summary=f"Page '{self._page_name(page.url)}' has no title tag",
                impact="Critical for SEO - page won't rank well and looks unprofessional in search results",
                recommendation="Add a unique, descriptive title tag (50-60 characters) to the page",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note="No <title> tag found"
                )],
                tags=["seo", "title", "critical"],
            )
            return

        title_len = len(title)

        # Title too long (will truncate in search results)
        if title_len > 70:
            self.add_finding(
                id="TEXT-TITLE-002",
                severity=Severity.P3,
                title=f"Page title may truncate in search ({title_len} chars)",
                summary=f"Title '{title[:50]}...' exceeds recommended length",
                impact="Important keywords may be cut off in search results, reducing click-through rate",
                recommendation="Keep title under 60 characters or front-load important keywords",
                effort=Effort.S,
                evidence=[self.evidence_with_metric(
                    url=page.url,
                    metric_name="title_length",
                    metric_value=title_len,
                    threshold=60
                )],
                tags=["seo", "title"],
            )

        # Title too short
        if title_len < 20:
            self.add_finding(
                id="TEXT-TITLE-003",
                severity=Severity.P3,
                title=f"Page title too brief ({title_len} chars)",
                summary=f"Title '{title}' doesn't fully describe page content",
                impact="Missed opportunity for keyword inclusion and search appeal",
                recommendation="Expand title to 50-60 characters with relevant keywords and brand",
                effort=Effort.S,
                evidence=[self.evidence_with_metric(
                    url=page.url,
                    metric_name="title_length",
                    metric_value=title_len,
                    threshold=30
                )],
                tags=["seo", "title"],
            )

        # Generic title patterns
        generic_patterns = [
            "home", "homepage", "welcome", "untitled",
            "page", "website", "site"
        ]
        title_lower = title.lower()
        if any(title_lower == pattern or title_lower == f"{pattern} page" for pattern in generic_patterns):
            self.add_finding(
                id="TEXT-TITLE-004",
                severity=Severity.P2,
                title="Generic page title detected",
                summary=f"Title '{title}' is not descriptive or unique",
                impact="Generic titles don't differentiate your page in search results",
                recommendation="Use a specific, keyword-rich title that describes the page content",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note=f"Generic title: '{title}'"
                )],
                tags=["seo", "title"],
            )

    def _check_heading_quality(self, page):
        """Check heading text quality."""
        h1s = page.headings.get("h1", [])

        for h1 in h1s:
            if not h1:
                continue

            h1_len = len(h1)

            # Very short H1
            if h1_len < 10:
                self.add_finding(
                    id="TEXT-H1-001",
                    severity=Severity.P3,
                    title=f"H1 heading too brief: '{h1}'",
                    summary="Primary heading doesn't fully communicate page topic",
                    impact="Weak topical signal for SEO and doesn't grab user attention",
                    recommendation="Expand H1 to clearly and compellingly describe page content (20-70 chars)",
                    effort=Effort.S,
                    evidence=[self.evidence_with_metric(
                        url=page.url,
                        metric_name="h1_length",
                        metric_value=h1_len,
                        threshold=20
                    )],
                    tags=["headings", "content"],
                )

            # Very long H1
            if h1_len > 100:
                self.add_finding(
                    id="TEXT-H1-002",
                    severity=Severity.P3,
                    title="H1 heading too long",
                    summary=f"H1 is {h1_len} characters: '{h1[:50]}...'",
                    impact="Long headings reduce scannability and visual impact",
                    recommendation="Keep H1 concise (under 70 characters) for better readability",
                    effort=Effort.S,
                    evidence=[self.evidence_with_metric(
                        url=page.url,
                        metric_name="h1_length",
                        metric_value=h1_len,
                        threshold=70
                    )],
                    tags=["headings", "ux"],
                )

            # H1 matches title exactly (missed opportunity)
            if page.title and h1.lower().strip() == page.title.lower().strip():
                self.add_finding(
                    id="TEXT-H1-003",
                    severity=Severity.P3,
                    title="H1 identical to page title",
                    summary=f"Both title and H1 are '{h1[:40]}...'",
                    impact="Missed opportunity to target additional keywords",
                    recommendation="Vary H1 slightly from title to cover more keyword variations",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(
                        url=page.url,
                        note="H1 exactly matches title tag"
                    )],
                    tags=["seo", "headings"],
                )

    def _check_cta_text_quality(self, page):
        """Check CTA text quality and effectiveness."""
        weak_cta_words = ["submit", "click", "click here", "here", "go", "send"]
        strong_cta_patterns = [
            "get", "start", "book", "contact", "request", "download",
            "try", "buy", "order", "schedule", "call", "learn", "discover",
            "explore", "see", "view", "join", "sign up", "subscribe"
        ]

        weak_ctas = []
        all_ctas = page.ctas + page.mobile_ctas

        for cta in all_ctas:
            text = cta.text.lower().strip()

            # Skip empty CTAs
            if not text:
                continue

            # Check for weak CTA text
            is_weak = any(weak in text for weak in weak_cta_words)
            is_strong = any(strong in text for strong in strong_cta_patterns)

            if is_weak and not is_strong:
                weak_ctas.append(cta.text)

        if weak_ctas:
            # Deduplicate
            unique_weak = list(set(weak_ctas))

            self.add_finding(
                id="TEXT-CTA-001",
                severity=Severity.P2,
                title=f"Weak CTA text detected ({len(unique_weak)} instance(s))",
                summary=f"CTAs use generic language: {', '.join(unique_weak[:3])}",
                impact="Weak CTAs have lower click-through rates and conversion",
                recommendation="Use action-oriented, benefit-focused text like 'Get Started', 'Book Now', 'Download Free Guide'",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note=f"Weak CTAs: {', '.join(unique_weak[:5])}"
                )],
                tags=["cta", "conversion", "copywriting"],
            )

        # Check for CTA visibility issues
        above_fold_ctas = [cta for cta in page.ctas if cta.is_above_fold]
        if all_ctas and not above_fold_ctas:
            self.add_finding(
                id="TEXT-CTA-002",
                severity=Severity.P2,
                title="No CTA visible above the fold",
                summary="All call-to-action buttons are below the initial viewport",
                impact="Users may not see CTAs without scrolling, reducing conversion",
                recommendation="Place primary CTA in the hero section, visible without scrolling",
                effort=Effort.M,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note="No above-fold CTAs detected"
                )],
                tags=["cta", "conversion", "ux"],
            )

    def _check_meta_description(self, page):
        """Check meta description quality."""
        meta = page.meta_tags
        description = meta.get("description", "")

        if not description:
            self.add_finding(
                id="TEXT-META-001",
                severity=Severity.P1,
                title="Missing meta description",
                summary=f"Page '{self._page_name(page.url)}' has no meta description",
                impact="Search engines may show random page text as snippet, reducing click-through",
                recommendation="Add a compelling meta description (150-160 chars) summarizing page content",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note="No meta description tag found"
                )],
                tags=["seo", "meta"],
            )
            return

        desc_len = len(description)

        # Description too short
        if desc_len < 70:
            self.add_finding(
                id="TEXT-META-002",
                severity=Severity.P3,
                title=f"Meta description too short ({desc_len} chars)",
                summary=f"Description: '{description}'",
                impact="Short descriptions waste valuable SERP real estate",
                recommendation="Expand to 150-160 characters with keywords and call-to-action",
                effort=Effort.S,
                evidence=[self.evidence_with_metric(
                    url=page.url,
                    metric_name="description_length",
                    metric_value=desc_len,
                    threshold=120
                )],
                tags=["seo", "meta"],
            )

        # Description too long
        if desc_len > 170:
            self.add_finding(
                id="TEXT-META-003",
                severity=Severity.P3,
                title=f"Meta description may truncate ({desc_len} chars)",
                summary=f"Description: '{description[:60]}...'",
                impact="Important information may be cut off in search results",
                recommendation="Keep meta description under 160 characters",
                effort=Effort.S,
                evidence=[self.evidence_with_metric(
                    url=page.url,
                    metric_name="description_length",
                    metric_value=desc_len,
                    threshold=160
                )],
                tags=["seo", "meta"],
            )
