"""SEO rules for technical SEO and content structure."""

from typing import List

from proofkit.schemas.finding import Finding, Severity, Category, Effort
from .base import BaseRule


class SEORules(BaseRule):
    """
    Rules for technical SEO and content structure.
    """

    category = Category.SEO

    def run(self) -> List[Finding]:
        """Execute all SEO rules."""
        self._check_h1_heading()
        self._check_title_tag()
        self._check_meta_description()
        self._check_heading_hierarchy()
        self._check_sitemap()
        self._check_robots_txt()
        self._check_canonical()
        self._check_internal_linking()
        self._check_image_alt()

        return self.findings

    def _check_h1_heading(self):
        """Check H1 heading presence and count."""
        for page in self.raw_data.snapshot.pages:
            h1s = page.headings.get("h1", [])

            if len(h1s) == 0:
                self.add_finding(
                    id="SEO-H1-001",
                    severity=Severity.P1,
                    title=f"Missing H1 heading on {self._page_name(page.url)}",
                    summary="Page has no H1 heading element",
                    impact="H1 is crucial for SEO - tells search engines the main topic. Missing H1 weakens page relevance signals.",
                    recommendation="Add single, descriptive H1 that includes primary keyword and describes page content",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url)],
                    tags=["headings", "on-page"],
                )
            elif len(h1s) > 1:
                self.add_finding(
                    id="SEO-H1-002",
                    severity=Severity.P2,
                    title=f"Multiple H1s detected ({len(h1s)}) on {self._page_name(page.url)}",
                    summary=f"Page has {len(h1s)} H1 headings instead of one",
                    impact="Multiple H1s dilute topical focus and confuse search engines about page hierarchy",
                    recommendation="Keep single H1 for main topic. Convert others to H2 or H3 as appropriate.",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(
                        page.url, note=f"H1s found: {', '.join(h1s[:3])}"
                    )],
                    tags=["headings", "structure"],
                )

    def _check_title_tag(self):
        """Check title tag presence and quality."""
        for page in self.raw_data.snapshot.pages:
            title = page.title

            if not title:
                self.add_finding(
                    id="SEO-TITLE-001",
                    severity=Severity.P0,
                    title=f"Missing page title on {self._page_name(page.url)}",
                    summary="Page has no title tag",
                    impact="Title is the most important on-page SEO element. Missing title severely hurts rankings and CTR.",
                    recommendation="Add descriptive title tag (50-60 characters) with primary keyword",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url)],
                    tags=["title", "critical"],
                )
            elif len(title) < 30:
                self.add_finding(
                    id="SEO-TITLE-002",
                    severity=Severity.P2,
                    title=f"Title too short ({len(title)} chars) on {self._page_name(page.url)}",
                    summary=f"Page title is only {len(title)} characters: '{title[:50]}'",
                    impact="Short titles miss opportunity to include keywords and attract clicks",
                    recommendation="Expand title to 50-60 characters with relevant keywords",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url, note=f"Title: {title}")],
                    tags=["title"],
                )
            elif len(title) > 70:
                self.add_finding(
                    id="SEO-TITLE-003",
                    severity=Severity.P3,
                    title=f"Title may be truncated ({len(title)} chars)",
                    summary=f"Page title is {len(title)} characters (may truncate in search results)",
                    impact="Titles over 60-70 characters get cut off in search results",
                    recommendation="Trim title to 60 characters or ensure important keywords are at start",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url, note=f"Title: {title[:70]}...")],
                    tags=["title"],
                )

    def _check_meta_description(self):
        """Check meta description presence and length."""
        for page in self.raw_data.snapshot.pages:
            description = page.meta_tags.get("description", "")

            if not description:
                self.add_finding(
                    id="SEO-DESC-001",
                    severity=Severity.P2,
                    title=f"Missing meta description on {self._page_name(page.url)}",
                    summary="Page has no meta description",
                    impact="Meta description affects CTR from search results. Google may generate one, but it may not be optimal.",
                    recommendation="Add compelling meta description (120-160 chars) with call-to-action",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url)],
                    tags=["meta", "description"],
                )
            elif len(description) < 70:
                self.add_finding(
                    id="SEO-DESC-002",
                    severity=Severity.P3,
                    title=f"Meta description too short ({len(description)} chars)",
                    summary=f"Description is only {len(description)} characters",
                    impact="Short descriptions don't fully utilize SERP real estate",
                    recommendation="Expand to 120-160 characters with compelling copy",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url, note=f"Description: {description}")],
                    tags=["meta", "description"],
                )
            elif len(description) > 160:
                self.add_finding(
                    id="SEO-DESC-003",
                    severity=Severity.P3,
                    title=f"Meta description may be truncated ({len(description)} chars)",
                    summary=f"Description is {len(description)} characters",
                    impact="Descriptions over 160 characters may be truncated in search results",
                    recommendation="Trim to 160 characters or front-load key information",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url)],
                    tags=["meta", "description"],
                )

    def _check_heading_hierarchy(self):
        """Check logical heading structure."""
        for page in self.raw_data.snapshot.pages:
            h1s = page.headings.get("h1", [])
            h2s = page.headings.get("h2", [])
            h3s = page.headings.get("h3", [])

            # H3 without H2
            if h3s and not h2s:
                self.add_finding(
                    id="SEO-HIER-001",
                    severity=Severity.P3,
                    title=f"Heading hierarchy issue on {self._page_name(page.url)}",
                    summary="H3 headings found without H2 headings",
                    impact="Improper heading hierarchy can confuse both users and search engines",
                    recommendation="Ensure logical heading flow: H1 → H2 → H3",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url)],
                    tags=["headings", "structure"],
                )

            # No subheadings
            if h1s and not h2s and not h3s:
                self.add_finding(
                    id="SEO-HIER-002",
                    severity=Severity.P3,
                    title=f"No subheadings on {self._page_name(page.url)}",
                    summary="Page has H1 but no H2 or H3 headings",
                    impact="Subheadings help structure content for both users and search engines",
                    recommendation="Add H2 subheadings to break up content and include secondary keywords",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url)],
                    tags=["headings", "structure"],
                    confidence=0.7,
                )

    def _check_sitemap(self):
        """Check sitemap.xml presence."""
        if not self.raw_data.http_probe.sitemap_exists:
            self.add_finding(
                id="SEO-SITEMAP-001",
                severity=Severity.P2,
                title="No sitemap.xml found",
                summary="sitemap.xml not accessible at standard location",
                impact="Sitemap helps search engines discover and index pages. Missing sitemap may slow indexing.",
                recommendation="Create and submit XML sitemap. Include in robots.txt. Submit to Google Search Console.",
                effort=Effort.S,
                evidence=[self.evidence_from_page(self.raw_data.url)],
                tags=["indexing", "crawling"],
            )

    def _check_robots_txt(self):
        """Check robots.txt presence and content."""
        robots = self.raw_data.http_probe.robots_txt

        if not robots:
            self.add_finding(
                id="SEO-ROBOTS-001",
                severity=Severity.P3,
                title="No robots.txt found",
                summary="robots.txt not accessible",
                impact="Without robots.txt, search engines use defaults. May crawl unnecessary pages.",
                recommendation="Create robots.txt with sitemap reference and any necessary disallow rules",
                effort=Effort.S,
                evidence=[self.evidence_from_page(self.raw_data.url)],
                tags=["crawling"],
            )
        elif "Disallow: /" in robots and "Allow:" not in robots:
            # Check if it's blocking all crawlers
            lines = robots.split("\n")
            blocking_all = False
            for i, line in enumerate(lines):
                if line.strip() == "Disallow: /":
                    # Check if there's a User-agent: * before it
                    for j in range(i - 1, -1, -1):
                        if lines[j].strip().lower().startswith("user-agent:"):
                            if "*" in lines[j]:
                                blocking_all = True
                            break
                    break

            if blocking_all:
                self.add_finding(
                    id="SEO-ROBOTS-002",
                    severity=Severity.P0,
                    title="robots.txt may be blocking all crawlers",
                    summary="Detected 'Disallow: /' for all user agents",
                    impact="This may prevent search engines from indexing the entire site!",
                    recommendation="Review robots.txt immediately. Ensure important pages are crawlable.",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(self.raw_data.url, note="robots.txt blocks crawling")],
                    tags=["critical", "indexing"],
                )

    def _check_canonical(self):
        """Check canonical URL implementation."""
        for page in self.raw_data.snapshot.pages:
            canonical = page.meta_tags.get("canonical", "")

            # No canonical on homepage is often fine
            if self._page_name(page.url) == "homepage":
                continue

            if not canonical:
                self.add_finding(
                    id="SEO-CANON-001",
                    severity=Severity.P3,
                    title=f"No canonical tag on {self._page_name(page.url)}",
                    summary="Page lacks canonical URL specification",
                    impact="May cause duplicate content issues if page is accessible via multiple URLs",
                    recommendation="Add <link rel='canonical'> pointing to preferred URL version",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url)],
                    tags=["canonical", "duplicate"],
                    confidence=0.6,
                )

    def _check_internal_linking(self):
        """Check internal linking structure."""
        for page in self.raw_data.snapshot.pages:
            if page.navigation:
                nav_links = len(page.navigation.links)

                if nav_links < 3:
                    self.add_finding(
                        id="SEO-LINK-001",
                        severity=Severity.P2,
                        title=f"Limited navigation on {self._page_name(page.url)}",
                        summary=f"Only {nav_links} navigation links found",
                        impact="Weak internal linking hurts both user navigation and SEO link equity distribution",
                        recommendation="Ensure comprehensive navigation with links to key sections",
                        effort=Effort.M,
                        evidence=[self.evidence_from_page(page.url)],
                        tags=["navigation", "internal-links"],
                    )

    def _check_image_alt(self):
        """Check for viewport meta tag (mobile-friendliness indicator)."""
        for page in self.raw_data.snapshot.pages:
            viewport = page.meta_tags.get("viewport", "")

            if not viewport:
                self.add_finding(
                    id="SEO-MOBILE-001",
                    severity=Severity.P1,
                    title=f"Missing viewport meta tag on {self._page_name(page.url)}",
                    summary="Page lacks viewport meta tag",
                    impact="Without viewport tag, mobile browsers may render page at desktop width. Hurts mobile SEO.",
                    recommendation="Add <meta name='viewport' content='width=device-width, initial-scale=1'>",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(page.url)],
                    tags=["mobile", "viewport"],
                )
                break  # Only report once
