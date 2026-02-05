"""Security rules for headers, SSL, and common vulnerabilities."""

from typing import List

from proofkit.schemas.finding import Finding, Severity, Category, Effort
from .base import BaseRule


class SecurityRules(BaseRule):
    """
    Rules for security headers and SSL.
    """

    category = Category.SECURITY

    def run(self) -> List[Finding]:
        """Execute all security rules."""
        self._check_https()
        self._check_hsts()
        self._check_content_security_policy()
        self._check_x_frame_options()
        self._check_other_headers()
        self._check_ssl_certificate()
        self._check_mixed_content()

        return self.findings

    def _check_https(self):
        """Check if site uses HTTPS."""
        final_url = self.raw_data.http_probe.final_url

        if not final_url.startswith("https://"):
            self.add_finding(
                id="SEC-HTTPS-001",
                severity=Severity.P0,
                title="Site not using HTTPS",
                summary="Website is served over unencrypted HTTP",
                impact="Browsers show 'Not Secure' warning. Google penalizes non-HTTPS sites. User data at risk.",
                recommendation="Install SSL certificate and redirect all HTTP to HTTPS immediately",
                effort=Effort.M,
                evidence=[self.evidence_from_page(final_url, note="Site served over HTTP")],
                tags=["ssl", "critical"],
            )

        # Check for HTTP to HTTPS redirect
        original_url = self.raw_data.http_probe.url
        if original_url.startswith("http://") and final_url.startswith("https://"):
            # Good - site redirects to HTTPS
            pass
        elif original_url.startswith("http://") and not final_url.startswith("https://"):
            self.add_finding(
                id="SEC-HTTPS-002",
                severity=Severity.P0,
                title="HTTP not redirecting to HTTPS",
                summary="HTTP version of site doesn't redirect to HTTPS",
                impact="Users accessing via HTTP remain on insecure connection",
                recommendation="Configure server to redirect all HTTP requests to HTTPS",
                effort=Effort.S,
                evidence=[self.evidence_from_page(original_url)],
                tags=["ssl", "redirect"],
            )

    def _check_hsts(self):
        """Check HTTP Strict Transport Security."""
        security = self.raw_data.http_probe.security_headers

        if not security.has_hsts:
            self.add_finding(
                id="SEC-HSTS-001",
                severity=Severity.P2,
                title="Missing HSTS header",
                summary="Strict-Transport-Security header not set",
                impact="Without HSTS, users could be vulnerable to SSL stripping and downgrade attacks",
                recommendation="Add header: Strict-Transport-Security: max-age=31536000; includeSubDomains",
                effort=Effort.S,
                evidence=[self.evidence_from_page(self.raw_data.url)],
                tags=["headers", "ssl"],
            )
        else:
            # Check HSTS configuration
            hsts_value = security.present.get("strict-transport-security", "")
            if "max-age=" in hsts_value:
                try:
                    max_age = int(hsts_value.split("max-age=")[1].split(";")[0].strip())
                    if max_age < 31536000:  # Less than 1 year
                        self.add_finding(
                            id="SEC-HSTS-002",
                            severity=Severity.P3,
                            title="HSTS max-age is short",
                            summary=f"HSTS max-age is {max_age} seconds (less than 1 year)",
                            impact="Short HSTS duration provides less protection",
                            recommendation="Set max-age to at least 31536000 (1 year) for better security",
                            effort=Effort.S,
                            tags=["headers", "hsts"],
                        )
                except (ValueError, IndexError):
                    pass

    def _check_content_security_policy(self):
        """Check Content Security Policy."""
        security = self.raw_data.http_probe.security_headers

        if not security.has_csp:
            self.add_finding(
                id="SEC-CSP-001",
                severity=Severity.P2,
                title="Missing Content-Security-Policy header",
                summary="No CSP header to prevent XSS attacks",
                impact="Site more vulnerable to cross-site scripting (XSS) attacks and data injection",
                recommendation="Implement Content-Security-Policy header. Start with report-only mode to test.",
                effort=Effort.M,
                evidence=[self.evidence_from_page(self.raw_data.url)],
                tags=["headers", "xss"],
            )

    def _check_x_frame_options(self):
        """Check X-Frame-Options header."""
        security = self.raw_data.http_probe.security_headers

        if not security.has_xframe:
            # Also check CSP frame-ancestors as modern alternative
            csp = security.present.get("content-security-policy", "")
            if "frame-ancestors" not in csp:
                self.add_finding(
                    id="SEC-XFRAME-001",
                    severity=Severity.P2,
                    title="Missing clickjacking protection",
                    summary="Neither X-Frame-Options nor CSP frame-ancestors is set",
                    impact="Site can be embedded in iframes on other domains, enabling clickjacking attacks",
                    recommendation="Add X-Frame-Options: SAMEORIGIN or CSP frame-ancestors directive",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(self.raw_data.url)],
                    tags=["headers", "clickjacking"],
                )

    def _check_other_headers(self):
        """Check other security headers."""
        security = self.raw_data.http_probe.security_headers

        # X-Content-Type-Options
        if "x-content-type-options" not in security.present:
            self.add_finding(
                id="SEC-XCTO-001",
                severity=Severity.P3,
                title="Missing X-Content-Type-Options header",
                summary="X-Content-Type-Options: nosniff not set",
                impact="Browsers may try to MIME-sniff responses, potentially executing malicious content",
                recommendation="Add header: X-Content-Type-Options: nosniff",
                effort=Effort.S,
                tags=["headers"],
            )

        # Referrer-Policy
        if "referrer-policy" not in security.present:
            self.add_finding(
                id="SEC-REF-001",
                severity=Severity.P3,
                title="Missing Referrer-Policy header",
                summary="No Referrer-Policy header set",
                impact="Full URLs including sensitive parameters may be sent to third parties",
                recommendation="Add header: Referrer-Policy: strict-origin-when-cross-origin",
                effort=Effort.S,
                tags=["headers", "privacy"],
            )

        # Overall security header score
        if security.score < 40:
            missing_list = ", ".join(security.missing[:5])
            self.add_finding(
                id="SEC-HEADERS-001",
                severity=Severity.P1,
                title=f"Multiple security headers missing (score: {security.score:.0f}/100)",
                summary=f"Security header score is only {security.score:.0f}/100",
                impact="Missing security headers leave site vulnerable to various attacks",
                recommendation=f"Add missing headers: {missing_list}",
                effort=Effort.M,
                evidence=[self.evidence_with_metric(
                    self.raw_data.url, "security_header_score", f"{security.score:.0f}%", "100%"
                )],
                tags=["headers"],
            )

    def _check_ssl_certificate(self):
        """Check SSL certificate validity."""
        ssl_info = self.raw_data.http_probe.ssl_info

        if ssl_info is None:
            return

        if not ssl_info.valid:
            self.add_finding(
                id="SEC-SSL-001",
                severity=Severity.P0,
                title="SSL certificate issue",
                summary=f"SSL problem: {ssl_info.error}",
                impact="Invalid SSL causes browser warnings and blocks access for many users. Destroys trust.",
                recommendation="Fix SSL certificate immediately. Check expiration, domain match, and certificate chain.",
                effort=Effort.M,
                evidence=[self.evidence_from_page(self.raw_data.url, note=ssl_info.error)],
                tags=["ssl", "critical"],
            )

        # Check certificate expiration
        if ssl_info.days_until_expiry is not None:
            if ssl_info.days_until_expiry < 0:
                self.add_finding(
                    id="SEC-SSL-002",
                    severity=Severity.P0,
                    title="SSL certificate has expired",
                    summary=f"Certificate expired {abs(ssl_info.days_until_expiry)} days ago",
                    impact="Browsers will show security warnings. Site may be inaccessible.",
                    recommendation="Renew SSL certificate immediately",
                    effort=Effort.S,
                    tags=["ssl", "critical", "expired"],
                )
            elif ssl_info.days_until_expiry < 14:
                self.add_finding(
                    id="SEC-SSL-003",
                    severity=Severity.P1,
                    title=f"SSL certificate expiring soon ({ssl_info.days_until_expiry} days)",
                    summary=f"Certificate expires in {ssl_info.days_until_expiry} days",
                    impact="Site will show security warnings when certificate expires",
                    recommendation="Renew SSL certificate now. Set up auto-renewal if possible.",
                    effort=Effort.S,
                    evidence=[self.evidence_with_metric(
                        self.raw_data.url, "ssl_expiry_days", ssl_info.days_until_expiry
                    )],
                    tags=["ssl", "expiring"],
                )
            elif ssl_info.days_until_expiry < 30:
                self.add_finding(
                    id="SEC-SSL-004",
                    severity=Severity.P2,
                    title=f"SSL certificate expiring in {ssl_info.days_until_expiry} days",
                    summary=f"Certificate expires: {ssl_info.expires}",
                    impact="Certificate will expire soon",
                    recommendation="Plan certificate renewal",
                    effort=Effort.S,
                    tags=["ssl"],
                )

    def _check_mixed_content(self):
        """Check for potential mixed content issues."""
        # Check if site is HTTPS but has console errors suggesting mixed content
        if self.raw_data.http_probe.final_url.startswith("https://"):
            for page in self.raw_data.snapshot.pages:
                mixed_content_errors = [
                    e for e in page.console_errors
                    if "mixed content" in e.lower() or "insecure" in e.lower()
                ]

                if mixed_content_errors:
                    self.add_finding(
                        id="SEC-MIXED-001",
                        severity=Severity.P1,
                        title="Mixed content detected",
                        summary="HTTPS page loads resources over HTTP",
                        impact="Mixed content can be blocked by browsers and shows security warnings",
                        recommendation="Update all resource URLs to HTTPS. Check images, scripts, stylesheets, iframes.",
                        effort=Effort.M,
                        evidence=[self.evidence_from_page(
                            page.url, note=mixed_content_errors[0][:100]
                        )],
                        tags=["ssl", "mixed-content"],
                    )
                    break
