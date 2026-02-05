# Analyzer Agent (Continued)

## 5. Performance Rules (continued from `proofkit/analyzer/rules/performance.py`)

```python
        elif score < 75:
            self.add_finding(
                id="PERF-SCORE-002",
                severity=Severity.P1,
                title=f"Performance score needs improvement: {score:.0f}/100",
                summary=f"Lighthouse performance score is {score:.0f} (target: 90+)",
                impact="Score below 75 may affect search rankings and user experience",
                recommendation="Focus on Core Web Vitals improvements: LCP, TBT/FID, CLS",
                effort=Effort.M,
                tags=["overall"],
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
        }
        return recommendations.get(opp_id, "See Lighthouse report for specific guidance.")
    
    def _get_opp_effort(self, opp_id: str) -> Effort:
        """Estimate effort for fixing opportunity."""
        easy = ["font-display", "uses-text-compression", "uses-long-cache-ttl"]
        hard = ["unused-javascript", "dom-size", "render-blocking-resources"]
        
        if opp_id in easy:
            return Effort.S
        elif opp_id in hard:
            return Effort.L
        return Effort.M
```

### 6. SEO Rules (`proofkit/analyzer/rules/seo.py`)

```python
from typing import List
from proofkit.schemas.finding import Finding, Severity, Category, Effort
from .base import BaseRule


class SEORules(BaseRule):
    """
    Rules for technical SEO and content structure.
    """
    
    category = Category.SEO
    
    def run(self) -> List[Finding]:
        self._check_h1_heading()
        self._check_meta_description()
        self._check_title_tag()
        self._check_heading_hierarchy()
        self._check_sitemap()
        self._check_robots_txt()
        self._check_canonical()
        self._check_internal_linking()
        
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
                    evidence=[self.evidence_from_page(page.url, note=f"H1s found: {h1s[:3]}")],
                    tags=["headings", "structure"],
                )
    
    def _check_meta_description(self):
        """Check meta description presence and length."""
        # Note: Would need to extract from HTML head
        # Simplified check based on Lighthouse data
        pass
    
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
                    tags=["title", "critical"],
                )
            elif len(title) < 30:
                self.add_finding(
                    id="SEO-TITLE-002",
                    severity=Severity.P2,
                    title=f"Title too short ({len(title)} chars)",
                    summary=f"Page title is only {len(title)} characters",
                    impact="Short titles miss opportunity to include keywords and attract clicks",
                    recommendation="Expand title to 50-60 characters with relevant keywords",
                    effort=Effort.S,
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
                    tags=["title"],
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
                    title="Heading hierarchy issue",
                    summary="H3 headings found without H2 headings",
                    impact="Improper heading hierarchy can confuse both users and search engines",
                    recommendation="Ensure logical heading flow: H1 → H2 → H3",
                    effort=Effort.S,
                    tags=["headings", "structure"],
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
                tags=["crawling"],
            )
        elif "Disallow: /" in robots and "Allow:" not in robots:
            self.add_finding(
                id="SEO-ROBOTS-002",
                severity=Severity.P0,
                title="robots.txt may be blocking all crawlers",
                summary="Detected 'Disallow: /' without Allow rules",
                impact="This may prevent search engines from indexing the entire site!",
                recommendation="Review robots.txt immediately. Ensure important pages are crawlable.",
                effort=Effort.S,
                tags=["critical", "indexing"],
            )
    
    def _check_canonical(self):
        """Check canonical URL implementation."""
        # Would need to extract from HTML head
        # Placeholder for implementation
        pass
    
    def _check_internal_linking(self):
        """Check internal linking structure."""
        total_pages = len(self.raw_data.snapshot.pages)
        
        for page in self.raw_data.snapshot.pages:
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
                    tags=["navigation", "internal-links"],
                )
    
    def _page_name(self, url: str) -> str:
        """Extract page name from URL."""
        path = url.rstrip("/").split("/")[-1]
        return path if path else "homepage"
```

### 7. Security Rules (`proofkit/analyzer/rules/security.py`)

```python
from typing import List
from proofkit.schemas.finding import Finding, Severity, Category, Effort
from .base import BaseRule


class SecurityRules(BaseRule):
    """
    Rules for security headers and SSL.
    """
    
    category = Category.SECURITY
    
    def run(self) -> List[Finding]:
        self._check_https()
        self._check_hsts()
        self._check_content_security_policy()
        self._check_x_frame_options()
        self._check_other_headers()
        self._check_ssl_certificate()
        
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
                tags=["ssl", "critical"],
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
                impact="Without HSTS, users could be vulnerable to downgrade attacks",
                recommendation="Add header: Strict-Transport-Security: max-age=31536000; includeSubDomains",
                effort=Effort.S,
                tags=["headers", "ssl"],
            )
    
    def _check_content_security_policy(self):
        """Check Content Security Policy."""
        security = self.raw_data.http_probe.security_headers
        
        if not security.has_csp:
            self.add_finding(
                id="SEC-CSP-001",
                severity=Severity.P2,
                title="Missing Content-Security-Policy header",
                summary="No CSP header to prevent XSS attacks",
                impact="Site more vulnerable to cross-site scripting (XSS) attacks",
                recommendation="Implement Content-Security-Policy header. Start with report-only mode to test.",
                effort=Effort.M,
                tags=["headers", "xss"],
            )
    
    def _check_x_frame_options(self):
        """Check X-Frame-Options header."""
        security = self.raw_data.http_probe.security_headers
        
        if not security.has_xframe:
            self.add_finding(
                id="SEC-XFRAME-001",
                severity=Severity.P2,
                title="Missing X-Frame-Options header",
                summary="Site can be embedded in iframes on other domains",
                impact="Vulnerable to clickjacking attacks where malicious sites overlay your content",
                recommendation="Add header: X-Frame-Options: SAMEORIGIN (or use CSP frame-ancestors)",
                effort=Effort.S,
                tags=["headers", "clickjacking"],
            )
    
    def _check_other_headers(self):
        """Check other security headers."""
        security = self.raw_data.http_probe.security_headers
        
        if security.score < 50:
            missing = ", ".join(security.missing[:5])
            self.add_finding(
                id="SEC-HEADERS-001",
                severity=Severity.P2,
                title=f"Multiple security headers missing",
                summary=f"Security header score: {security.score:.0f}/100",
                impact="Missing security headers leave site vulnerable to various attacks",
                recommendation=f"Add missing headers: {missing}",
                effort=Effort.M,
                tags=["headers"],
            )
    
    def _check_ssl_certificate(self):
        """Check SSL certificate validity."""
        ssl_info = self.raw_data.http_probe.ssl_info
        
        if ssl_info and not ssl_info.valid:
            self.add_finding(
                id="SEC-SSL-001",
                severity=Severity.P0,
                title="SSL certificate issue",
                summary=f"SSL problem: {ssl_info.error}",
                impact="Invalid SSL causes browser warnings and blocks access for many users",
                recommendation="Fix SSL certificate immediately. Check expiration, domain match, and chain.",
                effort=Effort.M,
                tags=["ssl", "critical"],
            )
```

### 8. Business Logic Rules (`proofkit/analyzer/rules/business_logic.py`)

```python
from typing import List, Optional
from proofkit.schemas.finding import Finding, Severity, Category, Effort
from proofkit.schemas.business import BusinessType, BUSINESS_FEATURES, FeatureStatus
from .base import BaseRule


class BusinessLogicRules(BaseRule):
    """
    Rules for business-specific feature verification.
    """
    
    category = Category.BUSINESS_LOGIC
    
    def run(self) -> List[Finding]:
        if not self.business_type:
            return self.findings
        
        expected = BUSINESS_FEATURES.get(self.business_type)
        if not expected:
            return self.findings
        
        self._check_must_have_features(expected.must_have)
        self._check_should_have_features(expected.should_have)
        
        return self.findings
    
    def _check_must_have_features(self, features: List[str]):
        """Check for critical business features."""
        for feature in features:
            status = self._detect_feature(feature)
            
            if status == FeatureStatus.MISSING:
                self.add_finding(
                    id=f"BIZ-MUST-{feature[:10].upper()}",
                    severity=Severity.P0,
                    title=f"Critical feature missing: {self._feature_display_name(feature)}",
                    summary=f"As a {self.business_type.value} website, '{feature}' is expected but not detected",
                    impact=f"This feature is essential for {self.business_type.value} websites. Missing it may cause complete conversion failure.",
                    recommendation=self._get_feature_recommendation(feature),
                    effort=Effort.M,
                    tags=["business-critical", self.business_type.value],
                )
            elif status == FeatureStatus.BROKEN:
                self.add_finding(
                    id=f"BIZ-BROKEN-{feature[:10].upper()}",
                    severity=Severity.P0,
                    title=f"Feature broken: {self._feature_display_name(feature)}",
                    summary=f"'{feature}' exists but doesn't appear to function correctly",
                    impact="Broken critical feature means users cannot complete their goal - 100% conversion loss on this path",
                    recommendation=f"Debug and fix {feature} functionality immediately",
                    effort=Effort.M,
                    tags=["broken", "critical"],
                )
            elif status == FeatureStatus.POORLY_PLACED:
                self.add_finding(
                    id=f"BIZ-PLACE-{feature[:10].upper()}",
                    severity=Severity.P1,
                    title=f"Feature poorly positioned: {self._feature_display_name(feature)}",
                    summary=f"'{feature}' exists but is not easily discoverable",
                    impact="Users may not find this feature, reducing conversion rate",
                    recommendation=f"Move {feature} to more prominent position (above fold or sticky)",
                    effort=Effort.S,
                    tags=["positioning", "ux"],
                )
    
    def _check_should_have_features(self, features: List[str]):
        """Check for recommended business features."""
        for feature in features:
            status = self._detect_feature(feature)
            
            if status == FeatureStatus.MISSING:
                self.add_finding(
                    id=f"BIZ-SHOULD-{feature[:10].upper()}",
                    severity=Severity.P2,
                    title=f"Recommended feature missing: {self._feature_display_name(feature)}",
                    summary=f"'{feature}' is common for {self.business_type.value} websites but not detected",
                    impact=f"Competitors likely have this feature. Missing it may put you at disadvantage.",
                    recommendation=self._get_feature_recommendation(feature),
                    effort=Effort.M,
                    confidence=0.7,
                    tags=["enhancement", self.business_type.value],
                )
    
    def _detect_feature(self, feature: str) -> FeatureStatus:
        """Detect if a feature exists and works."""
        # Map feature names to detection logic
        detection_map = {
            "inquiry_form": self._detect_inquiry_form,
            "whatsapp_cta": self._detect_whatsapp,
            "property_listings": self._detect_listings,
            "price_display": self._detect_prices,
            "image_gallery": self._detect_gallery,
            "location_map": self._detect_map,
            "virtual_tour": self._detect_virtual_tour,
            "add_to_cart": self._detect_cart,
            "checkout": self._detect_checkout,
            "search": self._detect_search,
            "booking_form": self._detect_booking,
        }
        
        detector = detection_map.get(feature)
        if detector:
            return detector()
        
        # Default: assume found with low confidence
        return FeatureStatus.FOUND
    
    def _detect_inquiry_form(self) -> FeatureStatus:
        """Detect inquiry/contact form."""
        for page in self.raw_data.snapshot.pages:
            if page.forms:
                return FeatureStatus.FOUND
        return FeatureStatus.MISSING
    
    def _detect_whatsapp(self) -> FeatureStatus:
        """Detect WhatsApp contact option."""
        for page in self.raw_data.snapshot.pages:
            if page.whatsapp_links:
                visible = any(w.get("is_visible") for w in page.whatsapp_links)
                if visible:
                    return FeatureStatus.FOUND
                return FeatureStatus.POORLY_PLACED
        return FeatureStatus.MISSING
    
    def _detect_listings(self) -> FeatureStatus:
        """Detect property/product listings."""
        # Check for listing-like patterns in content
        for page in self.raw_data.snapshot.pages:
            # Look for repeating content patterns (cards, grids)
            h2s = page.headings.get("h2", [])
            if len(h2s) >= 3:  # Multiple similar items
                return FeatureStatus.FOUND
        return FeatureStatus.MISSING
    
    def _detect_prices(self) -> FeatureStatus:
        """Detect price displays."""
        # Would check for currency symbols, price patterns
        return FeatureStatus.FOUND  # Simplified
    
    def _detect_gallery(self) -> FeatureStatus:
        """Detect image gallery."""
        return FeatureStatus.FOUND  # Simplified
    
    def _detect_map(self) -> FeatureStatus:
        """Detect location map."""
        return FeatureStatus.FOUND  # Simplified
    
    def _detect_virtual_tour(self) -> FeatureStatus:
        """Detect virtual tour integration."""
        return FeatureStatus.MISSING  # Simplified - would check for Matterport, etc.
    
    def _detect_cart(self) -> FeatureStatus:
        """Detect add to cart functionality."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                if "cart" in cta.text.lower() or "add" in cta.text.lower():
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING
    
    def _detect_checkout(self) -> FeatureStatus:
        """Detect checkout functionality."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                if "checkout" in cta.text.lower() or "pay" in cta.text.lower():
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING
    
    def _detect_search(self) -> FeatureStatus:
        """Detect search functionality."""
        # Would check for search input, magnifying glass icon
        return FeatureStatus.FOUND  # Simplified
    
    def _detect_booking(self) -> FeatureStatus:
        """Detect booking form."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                if "book" in cta.text.lower() or "reserve" in cta.text.lower():
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING
    
    def _feature_display_name(self, feature: str) -> str:
        """Convert feature key to display name."""
        return feature.replace("_", " ").title()
    
    def _get_feature_recommendation(self, feature: str) -> str:
        """Get recommendation for adding a feature."""
        recommendations = {
            "inquiry_form": "Add contact/inquiry form to key pages with minimal fields (Name, Email, Phone, Message)",
            "whatsapp_cta": "Add WhatsApp button in header and as floating sticky button. Use wa.me link.",
            "property_listings": "Create property/listing grid with key details: image, title, price, location",
            "price_display": "Display prices clearly. If pricing varies, show 'Starting from' or 'Contact for pricing'",
            "image_gallery": "Add image gallery with lightbox. Include multiple angles and details.",
            "location_map": "Embed Google Maps or Mapbox showing property/business location",
            "virtual_tour": "Consider adding Matterport or 360° virtual tour for immersive experience",
            "add_to_cart": "Implement add-to-cart functionality with clear feedback",
            "checkout": "Create streamlined checkout process with multiple payment options",
            "search": "Add search functionality to help users find content quickly",
            "booking_form": "Add booking/reservation form with date picker and availability check",
        }
        return recommendations.get(feature, f"Implement {feature} functionality")
```

### 9. Score Calculator (`proofkit/analyzer/scoring.py`)

```python
from typing import List, Dict
from proofkit.schemas.finding import Finding, Category, Severity
from proofkit.utils.config import get_config


class ScoreCalculator:
    """
    Calculate category and overall scores from findings.
    """
    
    # Severity impact on score (points deducted)
    SEVERITY_IMPACT = {
        "P0": 25,
        "P1": 15,
        "P2": 8,
        "P3": 3,
    }
    
    def __init__(self):
        self.config = get_config()
        self.weights = self.config.score_weights
    
    def calculate(self, findings: List[Finding]) -> Dict[str, int]:
        """
        Calculate scores for each category.
        
        Returns dict of category -> score (0-100)
        """
        # Group findings by category
        by_category: Dict[str, List[Finding]] = {}
        for f in findings:
            cat = f.category if isinstance(f.category, str) else f.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f)
        
        # Calculate score per category
        scores = {}
        for category in Category:
            cat_name = category.value
            cat_findings = by_category.get(cat_name, [])
            scores[cat_name] = self._category_score(cat_findings)
        
        # Calculate overall weighted score
        overall = self._overall_score(scores)
        scores["OVERALL"] = overall
        
        return scores
    
    def _category_score(self, findings: List[Finding]) -> int:
        """Calculate score for a single category."""
        if not findings:
            return 100  # No findings = perfect score
        
        # Start at 100, deduct based on findings
        score = 100
        
        for finding in findings:
            severity = finding.severity if isinstance(finding.severity, str) else finding.severity.value
            impact = self.SEVERITY_IMPACT.get(severity, 5)
            # Apply confidence factor
            impact *= finding.confidence
            score -= impact
        
        return max(0, min(100, int(score)))
    
    def _overall_score(self, category_scores: Dict[str, int]) -> int:
        """Calculate weighted overall score."""
        total_weight = 0
        weighted_sum = 0
        
        for category, weight in self.weights.items():
            if category in category_scores:
                weighted_sum += category_scores[category] * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0
        
        return int(weighted_sum / total_weight)
```

## Testing Requirements

```bash
# Tests for Analyzer Agent
tests/analyzer/
├── conftest.py              # Fixtures with sample RawData
├── test_engine.py           # Test rule orchestration
├── test_scoring.py          # Test score calculation
├── test_rules_conversion.py # Test conversion rules
├── test_rules_performance.py
├── test_rules_seo.py
├── test_rules_security.py
├── test_rules_business.py
```

## Your First Tasks (Phase 1 MVP)

1. [ ] Create `proofkit/analyzer/__init__.py` with Analyzer class
2. [ ] Implement `models.py` if needed for analyzer-specific types
3. [ ] Implement `rules/base.py` - BaseRule class
4. [ ] Implement `rules/conversion.py` - 5+ conversion rules
5. [ ] Implement `rules/performance.py` - Core Web Vitals rules
6. [ ] Implement `rules/seo.py` - Basic SEO rules
7. [ ] Implement `rules/security.py` - Security header rules
8. [ ] Implement `scoring.py` - Score calculation
9. [ ] Implement `engine.py` - Rule orchestration
10. [ ] Write tests for each rule category
11. [ ] Test with real RawData from Collector

## Interface Contract

### Input (from Collector Agent)
```python
from proofkit.collector.models import RawData

# You receive:
raw_data: RawData  # Contains snapshot, lighthouse, http_probe, business_signals
```

### Output (to Narrator Agent)
```python
from proofkit.schemas.finding import Finding

# You return:
findings: List[Finding]  # Sorted by severity, with evidence
scores: Dict[str, int]   # Category scores 0-100
```
