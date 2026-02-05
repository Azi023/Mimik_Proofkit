"""
DOM Quality Rules - Analyze HTML structure for quality issues.

Detects:
- Missing semantic HTML
- Heading structure problems
- Accessibility issues
- Navigation quality
- Image optimization signals
"""

from typing import List

from proofkit.schemas.finding import Finding, Severity, Category, Effort
from .base import BaseRule


class DOMQualityRules(BaseRule):
    """
    Analyze DOM structure for quality and maintainability issues.

    These checks are based on the collected page data and don't require
    vision APIs, making them fast and cost-effective.
    """

    category = Category.MAINTENANCE

    def run(self) -> List[Finding]:
        """Run DOM quality analysis."""
        for page in self.raw_data.snapshot.pages:
            self._check_semantic_html(page)
            self._check_heading_structure(page)
            self._check_navigation_quality(page)
            self._check_console_errors(page)
            self._check_meta_tags(page)

        return self.findings

    def _check_semantic_html(self, page):
        """Check for proper semantic HTML usage."""
        h1s = page.headings.get("h1", [])

        # Check for H1 presence
        if not h1s:
            self.add_finding(
                id="DOM-SEM-001",
                severity=Severity.P1,
                title="Missing primary heading (H1)",
                summary=f"Page '{self._page_name(page.url)}' lacks an H1 heading for content hierarchy",
                impact="Hurts SEO and accessibility. Screen readers rely on heading structure to navigate content.",
                recommendation="Add a single, descriptive H1 heading that summarizes the page's main topic",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note="No H1 element found on page"
                )],
                tags=["semantic", "accessibility", "seo"],
            )

    def _check_heading_structure(self, page):
        """Check heading hierarchy for issues."""
        h1s = page.headings.get("h1", [])
        h2s = page.headings.get("h2", [])
        h3s = page.headings.get("h3", [])

        # Multiple H1s
        if len(h1s) > 1:
            self.add_finding(
                id="DOM-HEAD-001",
                severity=Severity.P2,
                title=f"Multiple H1 headings detected ({len(h1s)})",
                summary=f"Page has {len(h1s)} H1 headings instead of one: {', '.join(h1s[:3])}{'...' if len(h1s) > 3 else ''}",
                impact="Dilutes topical focus for SEO and confuses the document outline for screen readers",
                recommendation="Keep a single H1 for the main topic. Convert other H1s to H2 or appropriate level",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note=f"Found H1s: {', '.join(h1s[:3])}"
                )],
                tags=["headings", "structure", "seo"],
            )

        # Skipped heading levels (H1 directly to H3)
        if h1s and h3s and not h2s:
            self.add_finding(
                id="DOM-HEAD-002",
                severity=Severity.P3,
                title="Heading level skipped (H1 → H3)",
                summary="Page has H3 headings without any H2 headings, breaking the logical hierarchy",
                impact="Screen readers announce heading levels; skipping levels is confusing for users",
                recommendation="Add H2 headings between H1 and H3 to create proper document structure",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note="Found H1 and H3 but no H2 headings"
                )],
                tags=["headings", "accessibility"],
            )

        # Empty H1
        for h1 in h1s:
            if not h1 or not h1.strip():
                self.add_finding(
                    id="DOM-HEAD-003",
                    severity=Severity.P1,
                    title="Empty H1 heading found",
                    summary="An H1 element exists but contains no text content",
                    impact="Search engines and screen readers expect meaningful H1 content",
                    recommendation="Add descriptive text to the H1 element",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(
                        url=page.url,
                        note="Empty H1 element detected"
                    )],
                    tags=["headings", "seo"],
                )
                break  # Only report once

    def _check_navigation_quality(self, page):
        """Check navigation link quality."""
        if not page.navigation:
            return

        nav_links = page.navigation.links

        # Very few navigation links
        if len(nav_links) < 3:
            self.add_finding(
                id="DOM-NAV-001",
                severity=Severity.P2,
                title="Limited navigation structure",
                summary=f"Only {len(nav_links)} navigation link(s) detected on the page",
                impact="Users may have difficulty finding important content sections",
                recommendation="Ensure navigation includes links to key pages: About, Services/Products, Contact, etc.",
                effort=Effort.M,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note=f"Found {len(nav_links)} nav links"
                )],
                tags=["navigation", "ux"],
            )

        # Check for generic/non-descriptive link text
        generic_texts = ["click here", "read more", "learn more", "here", "more", "link"]
        generic_found = []

        for link in nav_links:
            link_text = link.get("text", "").lower().strip()
            if link_text in generic_texts:
                generic_found.append(link_text)

        if generic_found:
            self.add_finding(
                id="DOM-NAV-002",
                severity=Severity.P3,
                title=f"Generic link text detected ({len(generic_found)} instances)",
                summary=f"Navigation contains non-descriptive link text: {', '.join(set(generic_found))}",
                impact="Poor accessibility - screen reader users hear 'click here' without context",
                recommendation="Use descriptive link text that explains the destination (e.g., 'View our services' instead of 'Click here')",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note=f"Generic links: {', '.join(generic_found[:5])}"
                )],
                tags=["accessibility", "links", "ux"],
            )

        # Check for broken hamburger menu
        if page.navigation.has_hamburger and page.hamburger_menu_works is False:
            self.add_finding(
                id="DOM-NAV-003",
                severity=Severity.P0,
                title="Mobile hamburger menu not functional",
                summary="The hamburger menu icon exists but doesn't open navigation on mobile",
                impact="Mobile users cannot access site navigation, severely impacting usability",
                recommendation="Fix JavaScript event handling for mobile menu toggle",
                effort=Effort.M,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note="Hamburger menu click did not reveal navigation"
                )],
                tags=["mobile", "navigation", "critical"],
            )

    def _check_console_errors(self, page):
        """Check for JavaScript console errors."""
        if not page.console_errors:
            return

        # Filter out common non-critical errors
        critical_errors = [
            err for err in page.console_errors
            if not any(ignore in err.lower() for ignore in [
                "favicon",
                "sourcemap",
                "deprecated",
                "third-party",
            ])
        ]

        if critical_errors:
            error_summary = critical_errors[0][:100]
            if len(critical_errors) > 1:
                error_summary += f" (+{len(critical_errors) - 1} more)"

            self.add_finding(
                id="DOM-JS-001",
                severity=Severity.P2 if len(critical_errors) < 3 else Severity.P1,
                title=f"JavaScript errors detected ({len(critical_errors)})",
                summary=f"Console errors found: {error_summary}",
                impact="JavaScript errors can break functionality and indicate code quality issues",
                recommendation="Review browser console and fix JavaScript errors",
                effort=Effort.M,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note=f"Errors: {'; '.join(critical_errors[:3])}"
                )],
                tags=["javascript", "errors", "quality"],
            )

    def _check_meta_tags(self, page):
        """Check for important meta tags."""
        meta = page.meta_tags

        # Check viewport meta tag
        if "viewport" not in meta:
            self.add_finding(
                id="DOM-META-001",
                severity=Severity.P1,
                title="Missing viewport meta tag",
                summary="Page doesn't have a viewport meta tag for responsive design",
                impact="Page won't render correctly on mobile devices",
                recommendation="Add <meta name='viewport' content='width=device-width, initial-scale=1'>",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note="No viewport meta tag found"
                )],
                tags=["mobile", "responsive", "meta"],
            )

        # Check charset
        if "charset" not in meta and "content-type" not in meta:
            self.add_finding(
                id="DOM-META-002",
                severity=Severity.P3,
                title="Character encoding not specified",
                summary="Page doesn't declare character encoding explicitly",
                impact="May cause character rendering issues in some browsers",
                recommendation="Add <meta charset='UTF-8'> in the <head> section",
                effort=Effort.S,
                evidence=[self.evidence_from_page(
                    url=page.url,
                    note="No charset meta tag found"
                )],
                tags=["encoding", "meta"],
            )
