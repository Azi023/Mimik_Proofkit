"""Performance rules based on Core Web Vitals and Lighthouse data."""

from typing import List, Optional

from proofkit.schemas.finding import Finding, Severity, Category, Effort
from .base import BaseRule


class PerformanceRules(BaseRule):
    """
    Rules for performance optimization based on Core Web Vitals and Lighthouse.
    """

    category = Category.PERFORMANCE

    # Core Web Vitals thresholds (Google's recommended values)
    CWV_THRESHOLDS = {
        "lcp": {"good": 2500, "poor": 4000},  # ms
        "fid": {"good": 100, "poor": 300},  # ms
        "cls": {"good": 0.1, "poor": 0.25},  # score
        "inp": {"good": 200, "poor": 500},  # ms
        "fcp": {"good": 1800, "poor": 3000},  # ms
        "ttfb": {"good": 800, "poor": 1800},  # ms
        "tbt": {"good": 200, "poor": 600},  # ms
        "si": {"good": 3400, "poor": 5800},  # ms
    }

    def run(self) -> List[Finding]:
        """Execute all performance rules."""
        self._check_lighthouse_score()
        self._check_lcp()
        self._check_cls()
        self._check_fid_tbt()
        self._check_fcp()
        self._check_ttfb()
        self._check_opportunities()

        return self.findings

    def _check_lighthouse_score(self):
        """Check overall Lighthouse performance score."""
        mobile_score = self.raw_data.lighthouse.mobile_scores.performance
        desktop_score = self.raw_data.lighthouse.desktop_scores.performance

        # Check mobile score (primary)
        if mobile_score is not None:
            if mobile_score < 50:
                self.add_finding(
                    id="PERF-SCORE-001",
                    severity=Severity.P0,
                    title=f"Critical mobile performance: {mobile_score:.0f}/100",
                    summary=f"Lighthouse mobile performance score is {mobile_score:.0f}",
                    impact="Score below 50 severely impacts user experience and SEO. Google uses mobile performance for rankings.",
                    recommendation="Address Core Web Vitals issues immediately. Focus on LCP, TBT, and CLS.",
                    effort=Effort.L,
                    evidence=[self.evidence_with_metric(
                        self.raw_data.url, "performance_score", mobile_score, 90
                    )],
                    tags=["lighthouse", "critical", "mobile"],
                )
            elif mobile_score < 75:
                self.add_finding(
                    id="PERF-SCORE-002",
                    severity=Severity.P1,
                    title=f"Mobile performance needs improvement: {mobile_score:.0f}/100",
                    summary=f"Lighthouse mobile performance score is {mobile_score:.0f} (target: 90+)",
                    impact="Score below 75 may affect search rankings and user experience",
                    recommendation="Focus on Core Web Vitals improvements: LCP, TBT/FID, CLS",
                    effort=Effort.M,
                    evidence=[self.evidence_with_metric(
                        self.raw_data.url, "performance_score", mobile_score, 90
                    )],
                    tags=["lighthouse", "mobile"],
                )
            elif mobile_score < 90:
                self.add_finding(
                    id="PERF-SCORE-003",
                    severity=Severity.P2,
                    title=f"Mobile performance could be better: {mobile_score:.0f}/100",
                    summary=f"Lighthouse mobile score is {mobile_score:.0f} (target: 90+)",
                    impact="Good performance, but improvements can further boost user experience",
                    recommendation="Review Lighthouse opportunities for remaining optimizations",
                    effort=Effort.M,
                    evidence=[self.evidence_with_metric(
                        self.raw_data.url, "performance_score", mobile_score, 90
                    )],
                    tags=["lighthouse", "mobile"],
                )

        # Check desktop vs mobile difference
        if mobile_score is not None and desktop_score is not None:
            diff = desktop_score - mobile_score
            if diff > 20:
                self.add_finding(
                    id="PERF-SCORE-004",
                    severity=Severity.P2,
                    title=f"Large desktop/mobile performance gap",
                    summary=f"Desktop: {desktop_score:.0f}, Mobile: {mobile_score:.0f} (diff: {diff:.0f})",
                    impact="Mobile users get significantly worse experience than desktop",
                    recommendation="Optimize specifically for mobile: reduce JS, optimize images, use responsive design",
                    effort=Effort.M,
                    tags=["lighthouse", "mobile-gap"],
                )

    def _check_lcp(self):
        """Check Largest Contentful Paint."""
        cwv = self.raw_data.lighthouse.mobile_cwv
        lcp = cwv.lcp

        if lcp is None:
            return

        thresholds = self.CWV_THRESHOLDS["lcp"]

        if lcp > thresholds["poor"]:
            self.add_finding(
                id="PERF-LCP-001",
                severity=Severity.P0,
                title=f"Critical LCP: {lcp/1000:.1f}s",
                summary=f"Largest Contentful Paint is {lcp/1000:.1f}s (should be <2.5s)",
                impact="LCP >4s means most users see a blank/loading screen for too long. High bounce rate.",
                recommendation="Optimize LCP element (usually hero image/text). Use preload, optimize images, reduce server time.",
                effort=Effort.M,
                evidence=[self.evidence_with_metric(self.raw_data.url, "LCP", f"{lcp/1000:.2f}s", "2.5s")],
                tags=["cwv", "lcp", "critical"],
            )
        elif lcp > thresholds["good"]:
            self.add_finding(
                id="PERF-LCP-002",
                severity=Severity.P1,
                title=f"LCP needs improvement: {lcp/1000:.1f}s",
                summary=f"Largest Contentful Paint is {lcp/1000:.1f}s (target: <2.5s)",
                impact="LCP between 2.5-4s affects user perception and SEO",
                recommendation="Identify LCP element in Lighthouse. Preload critical resources. Optimize images.",
                effort=Effort.M,
                evidence=[self.evidence_with_metric(self.raw_data.url, "LCP", f"{lcp/1000:.2f}s", "2.5s")],
                tags=["cwv", "lcp"],
            )

    def _check_cls(self):
        """Check Cumulative Layout Shift."""
        cwv = self.raw_data.lighthouse.mobile_cwv
        cls = cwv.cls

        if cls is None:
            return

        thresholds = self.CWV_THRESHOLDS["cls"]

        if cls > thresholds["poor"]:
            self.add_finding(
                id="PERF-CLS-001",
                severity=Severity.P0,
                title=f"Critical CLS: {cls:.3f}",
                summary=f"Cumulative Layout Shift is {cls:.3f} (should be <0.1)",
                impact="High CLS means content jumps around while loading. Users may click wrong elements.",
                recommendation="Add size attributes to images/videos. Reserve space for ads/embeds. Avoid inserting content above existing content.",
                effort=Effort.M,
                evidence=[self.evidence_with_metric(self.raw_data.url, "CLS", f"{cls:.3f}", "0.1")],
                tags=["cwv", "cls", "critical"],
            )
        elif cls > thresholds["good"]:
            self.add_finding(
                id="PERF-CLS-002",
                severity=Severity.P2,
                title=f"CLS needs improvement: {cls:.3f}",
                summary=f"Cumulative Layout Shift is {cls:.3f} (target: <0.1)",
                impact="Layout shifts hurt user experience and conversion rates",
                recommendation="Identify shifting elements. Set explicit dimensions. Use CSS aspect-ratio.",
                effort=Effort.S,
                evidence=[self.evidence_with_metric(self.raw_data.url, "CLS", f"{cls:.3f}", "0.1")],
                tags=["cwv", "cls"],
            )

    def _check_fid_tbt(self):
        """Check First Input Delay / Total Blocking Time."""
        cwv = self.raw_data.lighthouse.mobile_cwv
        tbt = cwv.tbt

        if tbt is None:
            return

        thresholds = self.CWV_THRESHOLDS["tbt"]

        if tbt > thresholds["poor"]:
            self.add_finding(
                id="PERF-TBT-001",
                severity=Severity.P1,
                title=f"High Total Blocking Time: {tbt:.0f}ms",
                summary=f"TBT is {tbt:.0f}ms (should be <200ms)",
                impact="High TBT means the page feels unresponsive. Users may think it's broken.",
                recommendation="Reduce JavaScript execution time. Split long tasks. Defer non-critical JS.",
                effort=Effort.L,
                evidence=[self.evidence_with_metric(self.raw_data.url, "TBT", f"{tbt:.0f}ms", "200ms")],
                tags=["cwv", "tbt", "interactivity"],
            )
        elif tbt > thresholds["good"]:
            self.add_finding(
                id="PERF-TBT-002",
                severity=Severity.P2,
                title=f"TBT could be improved: {tbt:.0f}ms",
                summary=f"Total Blocking Time is {tbt:.0f}ms (target: <200ms)",
                impact="Some users may experience slight delays in interaction",
                recommendation="Review long tasks in Chrome DevTools. Consider code splitting.",
                effort=Effort.M,
                evidence=[self.evidence_with_metric(self.raw_data.url, "TBT", f"{tbt:.0f}ms", "200ms")],
                tags=["cwv", "tbt"],
            )

    def _check_fcp(self):
        """Check First Contentful Paint."""
        cwv = self.raw_data.lighthouse.mobile_cwv
        fcp = cwv.fcp

        if fcp is None:
            return

        thresholds = self.CWV_THRESHOLDS["fcp"]

        if fcp > thresholds["poor"]:
            self.add_finding(
                id="PERF-FCP-001",
                severity=Severity.P1,
                title=f"Slow First Contentful Paint: {fcp/1000:.1f}s",
                summary=f"FCP is {fcp/1000:.1f}s (should be <1.8s)",
                impact="Users see blank screen for too long. High abandonment risk.",
                recommendation="Eliminate render-blocking resources. Inline critical CSS. Optimize server response.",
                effort=Effort.M,
                evidence=[self.evidence_with_metric(self.raw_data.url, "FCP", f"{fcp/1000:.2f}s", "1.8s")],
                tags=["fcp", "loading"],
            )

    def _check_ttfb(self):
        """Check Time to First Byte."""
        cwv = self.raw_data.lighthouse.mobile_cwv
        ttfb = cwv.ttfb

        if ttfb is None:
            return

        thresholds = self.CWV_THRESHOLDS["ttfb"]

        if ttfb > thresholds["poor"]:
            self.add_finding(
                id="PERF-TTFB-001",
                severity=Severity.P1,
                title=f"Slow server response: {ttfb:.0f}ms TTFB",
                summary=f"Time to First Byte is {ttfb:.0f}ms (should be <800ms)",
                impact="Slow TTFB delays everything else. Server is the bottleneck.",
                recommendation="Optimize server/database. Use CDN. Enable caching. Consider static generation.",
                effort=Effort.M,
                evidence=[self.evidence_with_metric(self.raw_data.url, "TTFB", f"{ttfb:.0f}ms", "800ms")],
                tags=["ttfb", "server"],
            )

    def _check_opportunities(self):
        """Check Lighthouse optimization opportunities."""
        opportunities = self.raw_data.lighthouse.opportunities

        if not opportunities:
            return

        for opp in opportunities[:5]:  # Top 5 opportunities
            if opp.savings_ms and opp.savings_ms > 500:
                severity = Severity.P1 if opp.savings_ms > 1000 else Severity.P2

                self.add_finding(
                    id=f"PERF-OPP-{opp.id[:15].upper()}",
                    severity=severity,
                    title=f"{opp.title}",
                    summary=f"{opp.display_value}" if opp.display_value else opp.description[:100],
                    impact=f"Fixing this could save ~{opp.savings_ms/1000:.1f}s of load time",
                    recommendation=self._get_opp_recommendation(opp.id),
                    effort=self._get_opp_effort(opp.id),
                    evidence=[self.evidence_with_metric(
                        self.raw_data.url, "potential_savings", f"{opp.savings_ms/1000:.1f}s"
                    )],
                    tags=["lighthouse", "opportunity"],
                )

    def _get_opp_recommendation(self, opp_id: str) -> str:
        """Get specific recommendation for Lighthouse opportunity."""
        recommendations = {
            "render-blocking-resources": "Defer non-critical CSS/JS. Inline critical CSS. Use async/defer attributes.",
            "unused-css-rules": "Remove unused CSS. Use PurgeCSS or similar tool. Split CSS by route.",
            "unused-javascript": "Remove unused JS. Use code splitting. Tree-shake dependencies.",
            "modern-image-formats": "Convert images to WebP or AVIF. Use picture element for fallbacks.",
            "uses-optimized-images": "Compress images. Use appropriate quality settings (80-85% for JPEG).",
            "uses-responsive-images": "Add srcset and sizes attributes. Serve appropriately sized images.",
            "uses-text-compression": "Enable GZIP or Brotli compression on server.",
            "uses-long-cache-ttl": "Set Cache-Control headers with long max-age for static assets.",
            "font-display": "Add font-display: swap to @font-face rules. Preload critical fonts.",
            "dom-size": "Reduce DOM complexity. Virtualize long lists. Lazy load sections.",
            "offscreen-images": "Lazy load images below the fold. Use loading='lazy' attribute.",
            "unminified-css": "Minify CSS files. Use build tools like PostCSS.",
            "unminified-javascript": "Minify JavaScript. Use Terser or similar tool.",
            "legacy-javascript": "Serve modern JavaScript to modern browsers. Use module/nomodule pattern.",
            "efficient-animated-content": "Use video instead of GIF. Optimize video encoding.",
            "uses-rel-preconnect": "Add preconnect hints for third-party origins.",
            "server-response-time": "Optimize server response. Use CDN. Enable caching.",
            "redirects": "Minimize redirect chains. Update links to final destinations.",
            "total-byte-weight": "Reduce total page weight. Compress assets. Remove unused code.",
        }
        return recommendations.get(opp_id, "See Lighthouse report for specific guidance.")

    def _get_opp_effort(self, opp_id: str) -> Effort:
        """Estimate effort for fixing opportunity."""
        easy = ["font-display", "uses-text-compression", "uses-long-cache-ttl", "offscreen-images"]
        hard = ["unused-javascript", "dom-size", "render-blocking-resources", "legacy-javascript"]

        if opp_id in easy:
            return Effort.S
        elif opp_id in hard:
            return Effort.L
        return Effort.M
