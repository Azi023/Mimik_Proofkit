"""UX rules for user experience and usability."""

from typing import List

from proofkit.schemas.finding import Finding, Severity, Category, Effort
from .base import BaseRule


class UXRules(BaseRule):
    """
    Rules for user experience and usability.
    """

    category = Category.UX

    def run(self) -> List[Finding]:
        """Execute all UX rules."""
        self._check_mobile_navigation()
        self._check_hamburger_menu()
        self._check_navigation_depth()
        self._check_console_errors()
        self._check_page_structure()

        return self.findings

    def _check_mobile_navigation(self):
        """Check mobile navigation functionality."""
        homepage = self._get_homepage()

        if homepage and homepage.navigation:
            # Check if hamburger menu exists on mobile
            if not homepage.navigation.has_hamburger:
                # Check if desktop has many nav items
                if len(homepage.navigation.links) > 5:
                    self.add_finding(
                        id="UX-NAV-001",
                        severity=Severity.P2,
                        title="No mobile menu detected",
                        summary="Site has many navigation links but no hamburger/mobile menu detected",
                        impact="Mobile users may have difficulty navigating if menu doesn't collapse properly",
                        recommendation="Implement hamburger menu for mobile with clear toggle button",
                        effort=Effort.M,
                        evidence=[self.evidence_from_page(homepage.url)],
                        tags=["mobile", "navigation"],
                        confidence=0.7,
                    )

    def _check_hamburger_menu(self):
        """Check if hamburger menu works correctly."""
        homepage = self._get_homepage()

        if homepage and homepage.hamburger_menu_works is False:
            self.add_finding(
                id="UX-MENU-001",
                severity=Severity.P1,
                title="Hamburger menu not working",
                summary="Mobile menu button detected but navigation doesn't appear when clicked",
                impact="Mobile users cannot access navigation - severely limits site usability on mobile",
                recommendation="Debug hamburger menu JavaScript. Ensure nav becomes visible on click.",
                effort=Effort.M,
                evidence=[self.evidence_from_page(homepage.url)],
                tags=["mobile", "navigation", "broken"],
            )

    def _check_navigation_depth(self):
        """Check navigation depth and usability."""
        for page in self.raw_data.snapshot.pages:
            if page.navigation:
                nav_links = page.navigation.links

                # Too few links
                if len(nav_links) == 0:
                    self.add_finding(
                        id="UX-NAV-002",
                        severity=Severity.P1,
                        title=f"No navigation detected on {self._page_name(page.url)}",
                        summary="Page appears to have no navigation menu",
                        impact="Users have no way to navigate to other pages",
                        recommendation="Add clear navigation with links to key sections",
                        effort=Effort.M,
                        evidence=[self.evidence_from_page(page.url)],
                        tags=["navigation"],
                    )
                elif len(nav_links) < 3:
                    self.add_finding(
                        id="UX-NAV-003",
                        severity=Severity.P2,
                        title=f"Very limited navigation ({len(nav_links)} links)",
                        summary=f"Navigation only has {len(nav_links)} links",
                        impact="Users may not find important sections of the site",
                        recommendation="Expand navigation to include all key sections: About, Services, Contact, etc.",
                        effort=Effort.S,
                        evidence=[self.evidence_from_page(page.url)],
                        tags=["navigation"],
                    )

    def _check_console_errors(self):
        """Check for JavaScript console errors."""
        total_errors = 0
        pages_with_errors = []

        for page in self.raw_data.snapshot.pages:
            if page.console_errors:
                total_errors += len(page.console_errors)
                pages_with_errors.append(page.url)

        if total_errors > 0:
            severity = Severity.P1 if total_errors > 5 else Severity.P2
            sample_errors = []
            for page in self.raw_data.snapshot.pages:
                sample_errors.extend(page.console_errors[:2])
                if len(sample_errors) >= 3:
                    break

            self.add_finding(
                id="UX-JS-001",
                severity=severity,
                title=f"JavaScript errors detected ({total_errors} total)",
                summary=f"Found {total_errors} console errors across {len(pages_with_errors)} pages",
                impact="JavaScript errors can break functionality and create poor user experience",
                recommendation="Review and fix console errors. Check browser DevTools for details.",
                effort=Effort.M,
                evidence=[self.evidence_from_page(
                    pages_with_errors[0] if pages_with_errors else self.raw_data.url,
                    note=f"Errors: {'; '.join(sample_errors[:2])}"[:200]
                )],
                tags=["javascript", "errors"],
            )

    def _check_page_structure(self):
        """Check basic page structure quality."""
        homepage = self._get_homepage()

        if homepage:
            # Check for empty-looking pages
            h1s = homepage.headings.get("h1", [])
            h2s = homepage.headings.get("h2", [])

            if not h1s and not h2s and not homepage.ctas:
                self.add_finding(
                    id="UX-STRUCT-001",
                    severity=Severity.P1,
                    title="Homepage appears to lack content structure",
                    summary="No headings or CTAs detected on homepage",
                    impact="Users may not understand what the site offers or what action to take",
                    recommendation="Add clear heading hierarchy and prominent calls-to-action",
                    effort=Effort.M,
                    evidence=[self.evidence_from_page(homepage.url)],
                    tags=["structure", "content"],
                )

    def _check_forms_ux(self):
        """Check form user experience."""
        for page in self.raw_data.snapshot.pages:
            for form in page.forms:
                # Forms with many required fields
                if form.required_count > 5:
                    self.add_finding(
                        id="UX-FORM-001",
                        severity=Severity.P2,
                        title=f"Form has many required fields ({form.required_count})",
                        summary=f"Form requires {form.required_count} fields to be filled",
                        impact="High friction forms reduce completion rates",
                        recommendation="Reduce required fields to minimum. Collect more info later.",
                        effort=Effort.S,
                        evidence=[self.evidence_from_page(page.url)],
                        tags=["form", "friction"],
                    )
