# Collector Agent

## Identity

You are the **Collector Agent** for Mimik ProofKit. You own all data collection modules: Playwright browser automation, Lighthouse performance audits, and HTTP probing.

## Your Scope

### Files You Own
```
proofkit/collector/
├── __init__.py              # Collector class + exports
├── playwright_snapshot.py   # DOM extraction, screenshots, CTA detection
├── lighthouse.py            # Performance metrics, Core Web Vitals
├── http_probe.py            # Headers, SSL, redirects, security
├── stack_detector.py        # CMS, framework, analytics detection
├── business_detector.py     # Auto-detect business type from content
├── feature_verifier.py      # Verify expected features work
└── models.py                # Collector-specific data models
```

### Files You Don't Touch
- `proofkit/cli/*` (Backend Agent)
- `proofkit/schemas/*` (Backend Agent - but you import from here)
- `proofkit/analyzer/*` (Analyzer Agent)
- `proofkit/narrator/*` (Narrator Agent)

## Core Responsibilities

### 1. Main Collector Interface (`proofkit/collector/__init__.py`)

```python
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from proofkit.schemas.audit import AuditMode
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import CollectorError

from .playwright_snapshot import PlaywrightCollector
from .lighthouse import LighthouseCollector
from .http_probe import HttpProbeCollector
from .stack_detector import StackDetector
from .business_detector import BusinessDetector
from .models import RawData, SnapshotData, LighthouseData, HttpProbeData


class Collector:
    """
    Main collector that orchestrates all data collection.
    """
    
    def __init__(self):
        self.playwright = PlaywrightCollector()
        self.lighthouse = LighthouseCollector()
        self.http_probe = HttpProbeCollector()
        self.stack_detector = StackDetector()
        self.business_detector = BusinessDetector()
    
    def collect(
        self,
        url: str,
        mode: AuditMode,
        output_dir: Path,
    ) -> RawData:
        """
        Collect all raw data for a URL.
        
        Args:
            url: Target URL to audit
            mode: fast (homepage + key pages) or full (crawl)
            output_dir: Where to save raw data and screenshots
            
        Returns:
            RawData containing all collected information
        """
        logger.info(f"Starting collection for {url} in {mode} mode")
        
        # Determine pages to audit
        pages = self._get_pages_to_audit(url, mode)
        
        # Run collectors in sequence (parallel later)
        snapshot = self.playwright.collect(url, pages, output_dir)
        lighthouse = self.lighthouse.collect(url, output_dir)
        http_probe = self.http_probe.collect(url)
        stack = self.stack_detector.detect(snapshot)
        business_signals = self.business_detector.detect(snapshot)
        
        raw_data = RawData(
            url=url,
            mode=mode,
            pages_audited=pages,
            snapshot=snapshot,
            lighthouse=lighthouse,
            http_probe=http_probe,
            detected_stack=stack,
            business_signals=business_signals,
        )
        
        # Save raw data
        self._save_raw_data(raw_data, output_dir)
        
        return raw_data
    
    def _get_pages_to_audit(self, url: str, mode: AuditMode) -> list[str]:
        """Determine which pages to audit based on mode."""
        if mode == AuditMode.FAST:
            # Homepage + discover key pages from nav
            return self.playwright.discover_key_pages(url, max_pages=5)
        else:
            # Full crawl
            return self.playwright.crawl_site(url, max_pages=50)
    
    def _save_raw_data(self, data: RawData, output_dir: Path):
        """Save collected data to JSON files."""
        import json
        
        (output_dir / "snapshot.json").write_text(
            data.snapshot.model_dump_json(indent=2)
        )
        (output_dir / "lighthouse_mobile.json").write_text(
            json.dumps(data.lighthouse.mobile, indent=2)
        )
        (output_dir / "lighthouse_desktop.json").write_text(
            json.dumps(data.lighthouse.desktop, indent=2)
        )
        (output_dir / "http_probe.json").write_text(
            data.http_probe.model_dump_json(indent=2)
        )
```

### 2. Playwright Snapshot (`proofkit/collector/playwright_snapshot.py`)

```python
import re
from pathlib import Path
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Page, Browser

from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import PlaywrightError
from .models import SnapshotData, PageSnapshot, CTAInfo, FormInfo, NavigationInfo


# Detection patterns
WHATSAPP_PATTERNS = [
    r"wa\.me\/",
    r"api\.whatsapp\.com\/send",
    r"whatsapp:\/\/send",
]

CTA_KEYWORDS = [
    "contact", "call", "whatsapp", "book", "get quote", "get a quote",
    "inquire", "enquire", "submit", "request", "buy", "shop", "order",
    "schedule", "start", "try", "demo", "free trial", "sign up", "register",
]

BUSINESS_KEYWORDS = {
    "real_estate": ["property", "apartment", "villa", "bedroom", "sqft", "floor plan", "price", "location", "for sale", "for rent"],
    "ecommerce": ["add to cart", "buy now", "checkout", "product", "shop", "shipping", "cart"],
    "saas": ["pricing", "free trial", "sign up", "demo", "features", "integrations", "api"],
    "hospitality": ["book now", "reservation", "check-in", "rooms", "amenities", "guests", "hotel"],
    "restaurant": ["menu", "order", "delivery", "reservation", "table", "cuisine", "dine"],
}


class PlaywrightCollector:
    """
    Browser-based data collection using Playwright.
    """
    
    def __init__(self):
        self.config = get_config()
        self.timeout = self.config.playwright_timeout
    
    def collect(
        self,
        url: str,
        pages: List[str],
        output_dir: Path,
    ) -> SnapshotData:
        """
        Collect DOM data and screenshots for specified pages.
        """
        page_snapshots = []
        screenshots = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            for page_url in pages:
                try:
                    snapshot = self._snapshot_page(browser, page_url, output_dir)
                    page_snapshots.append(snapshot)
                    screenshots.extend(snapshot.screenshots)
                except Exception as e:
                    logger.warning(f"Failed to snapshot {page_url}: {e}")
            
            browser.close()
        
        return SnapshotData(
            url=url,
            pages=page_snapshots,
            screenshots=screenshots,
            total_ctas=sum(len(p.ctas) for p in page_snapshots),
            total_forms=sum(len(p.forms) for p in page_snapshots),
        )
    
    def _snapshot_page(
        self,
        browser: Browser,
        url: str,
        output_dir: Path,
    ) -> PageSnapshot:
        """Snapshot a single page."""
        
        # Desktop viewport
        desktop_page = browser.new_page(viewport={"width": 1440, "height": 900})
        desktop_page.goto(url, wait_until="networkidle", timeout=self.timeout)
        
        # Scroll to trigger lazy content
        self._scroll_page(desktop_page)
        
        # Extract data
        title = self._get_title(desktop_page)
        headings = self._get_headings(desktop_page)
        ctas = self._get_ctas(desktop_page)
        forms = self._get_forms(desktop_page)
        navigation = self._get_navigation(desktop_page)
        whatsapp = self._get_whatsapp_links(desktop_page)
        contact_info = self._get_contact_info(desktop_page)
        
        # Screenshots
        page_name = self._url_to_filename(url)
        desktop_screenshot = output_dir / f"{page_name}_desktop.png"
        desktop_page.screenshot(path=str(desktop_screenshot), full_page=True)
        
        # Mobile viewport
        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        mobile_page.goto(url, wait_until="networkidle", timeout=self.timeout)
        self._scroll_page(mobile_page)
        
        mobile_screenshot = output_dir / f"{page_name}_mobile.png"
        mobile_page.screenshot(path=str(mobile_screenshot), full_page=True)
        
        # Check mobile-specific issues
        mobile_ctas = self._get_ctas(mobile_page)
        hamburger_works = self._test_hamburger_menu(mobile_page)
        
        desktop_page.close()
        mobile_page.close()
        
        return PageSnapshot(
            url=url,
            title=title,
            headings=headings,
            ctas=ctas,
            mobile_ctas=mobile_ctas,
            forms=forms,
            navigation=navigation,
            whatsapp_links=whatsapp,
            contact_info=contact_info,
            screenshots=[str(desktop_screenshot), str(mobile_screenshot)],
            hamburger_menu_works=hamburger_works,
            console_errors=self._get_console_errors(desktop_page),
        )
    
    def _scroll_page(self, page: Page, scrolls: int = 3):
        """Scroll page to trigger lazy loading."""
        for _ in range(scrolls):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(500)
    
    def _get_title(self, page: Page) -> str:
        return page.title().strip()
    
    def _get_headings(self, page: Page) -> Dict[str, List[str]]:
        """Extract H1-H3 headings."""
        return {
            "h1": [h.strip() for h in page.locator("h1").all_inner_texts() if h.strip()],
            "h2": [h.strip() for h in page.locator("h2").all_inner_texts() if h.strip()],
            "h3": [h.strip() for h in page.locator("h3").all_inner_texts() if h.strip()],
        }
    
    def _get_ctas(self, page: Page) -> List[CTAInfo]:
        """Extract CTA buttons and links."""
        ctas = []
        
        # Check links
        for link in page.locator("a").all():
            try:
                text = (link.inner_text() or "").strip().lower()
                href = link.get_attribute("href") or ""
                
                if any(kw in text for kw in CTA_KEYWORDS):
                    bbox = link.bounding_box()
                    ctas.append(CTAInfo(
                        text=text,
                        type="link",
                        href=href,
                        is_visible=link.is_visible(),
                        is_above_fold=bbox["y"] < 900 if bbox else False,
                        selector=self._get_selector(link),
                    ))
            except Exception:
                continue
        
        # Check buttons
        for button in page.locator("button").all():
            try:
                text = (button.inner_text() or "").strip().lower()
                
                if any(kw in text for kw in CTA_KEYWORDS):
                    bbox = button.bounding_box()
                    ctas.append(CTAInfo(
                        text=text,
                        type="button",
                        href=None,
                        is_visible=button.is_visible(),
                        is_above_fold=bbox["y"] < 900 if bbox else False,
                        selector=self._get_selector(button),
                    ))
            except Exception:
                continue
        
        return ctas[:30]  # Limit to avoid huge lists
    
    def _get_whatsapp_links(self, page: Page) -> List[Dict]:
        """Find WhatsApp contact options."""
        whatsapp_links = []
        
        for link in page.locator("a").all():
            try:
                href = link.get_attribute("href") or ""
                text = (link.inner_text() or "").strip()
                
                if any(re.search(p, href, re.IGNORECASE) for p in WHATSAPP_PATTERNS):
                    whatsapp_links.append({
                        "text": text,
                        "href": href,
                        "is_visible": link.is_visible(),
                    })
                elif "whatsapp" in text.lower():
                    whatsapp_links.append({
                        "text": text,
                        "href": href,
                        "is_visible": link.is_visible(),
                    })
            except Exception:
                continue
        
        return whatsapp_links
    
    def _get_forms(self, page: Page) -> List[FormInfo]:
        """Analyze forms on the page."""
        forms = []
        
        for form in page.locator("form").all():
            try:
                inputs = form.locator("input, textarea, select").all()
                required_count = sum(
                    1 for inp in inputs 
                    if inp.get_attribute("required") is not None
                )
                
                forms.append(FormInfo(
                    action=form.get_attribute("action"),
                    method=form.get_attribute("method") or "GET",
                    field_count=len(inputs),
                    required_count=required_count,
                    has_email_field=any(
                        inp.get_attribute("type") == "email" or 
                        "email" in (inp.get_attribute("name") or "").lower()
                        for inp in inputs
                    ),
                    has_phone_field=any(
                        inp.get_attribute("type") == "tel" or
                        "phone" in (inp.get_attribute("name") or "").lower()
                        for inp in inputs
                    ),
                    submit_button_text=self._get_submit_button_text(form),
                ))
            except Exception:
                continue
        
        return forms
    
    def _get_navigation(self, page: Page) -> NavigationInfo:
        """Extract navigation structure."""
        nav_links = []
        
        # Try common nav selectors
        for selector in ["nav a", "header a", "[role='navigation'] a"]:
            links = page.locator(selector).all()
            if links:
                for link in links[:20]:
                    try:
                        text = (link.inner_text() or "").strip()
                        href = link.get_attribute("href") or ""
                        if text and href:
                            nav_links.append({"text": text, "href": href})
                    except Exception:
                        continue
                break
        
        return NavigationInfo(
            links=nav_links,
            has_hamburger=page.locator("[class*='hamburger'], [class*='mobile-menu'], [aria-label*='menu']").count() > 0,
            depth=self._estimate_nav_depth(nav_links),
        )
    
    def _get_contact_info(self, page: Page) -> Dict:
        """Extract contact information."""
        html = page.content()
        
        # Phone patterns
        phone_pattern = r'(?:\+?[\d\s\-().]{10,})'
        phones = re.findall(phone_pattern, html)
        
        # Email patterns
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, html)
        
        return {
            "phones": list(set(phones))[:5],
            "emails": list(set(emails))[:5],
            "has_tel_link": 'href="tel:' in html,
            "has_mailto_link": 'href="mailto:' in html,
        }
    
    def _test_hamburger_menu(self, page: Page) -> Optional[bool]:
        """Test if hamburger menu works on mobile."""
        hamburger = page.locator("[class*='hamburger'], [class*='mobile-menu'], button[aria-label*='menu']").first
        
        if hamburger.count() == 0:
            return None
        
        try:
            hamburger.click()
            page.wait_for_timeout(500)
            
            # Check if nav appeared
            nav_visible = page.locator("nav, [role='navigation']").first.is_visible()
            return nav_visible
        except Exception:
            return False
    
    def _get_console_errors(self, page: Page) -> List[str]:
        """Capture JavaScript console errors."""
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        return errors[:10]
    
    def _get_selector(self, element) -> str:
        """Generate a selector for an element."""
        # Simplified - in production use a more robust approach
        try:
            return element.evaluate("el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ')[0] : '')")
        except Exception:
            return ""
    
    def _get_submit_button_text(self, form) -> str:
        """Get text of form's submit button."""
        try:
            submit = form.locator("button[type='submit'], input[type='submit']").first
            return (submit.inner_text() or submit.get_attribute("value") or "Submit").strip()
        except Exception:
            return "Submit"
    
    def _estimate_nav_depth(self, links: List[Dict]) -> int:
        """Estimate navigation depth from link structure."""
        return min(3, len(links) // 5 + 1)
    
    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename."""
        return re.sub(r'[^\w\-]', '_', url.split("//")[-1])[:50]
    
    def discover_key_pages(self, url: str, max_pages: int = 5) -> List[str]:
        """Discover key pages from navigation."""
        pages = [url]
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=self.timeout)
            
            nav = self._get_navigation(page)
            
            # Prioritize important pages
            priority_keywords = ["contact", "about", "services", "product", "pricing", "property", "portfolio"]
            
            for link in nav.links:
                href = link.get("href", "")
                text = link.get("text", "").lower()
                
                if href.startswith("http") and any(kw in text or kw in href.lower() for kw in priority_keywords):
                    if href not in pages:
                        pages.append(href)
                
                if len(pages) >= max_pages:
                    break
            
            browser.close()
        
        return pages
    
    def crawl_site(self, url: str, max_pages: int = 50) -> List[str]:
        """Full site crawl - discover all internal pages."""
        # Implementation for full mode
        # Uses breadth-first crawl following internal links
        pass
```

### 3. Lighthouse Module (`proofkit/collector/lighthouse.py`)

```python
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any

from proofkit.utils.logger import logger
from proofkit.utils.exceptions import LighthouseError
from .models import LighthouseData, CoreWebVitals, LighthouseOpportunity


class LighthouseCollector:
    """
    Lighthouse performance audit collector.
    """
    
    def collect(self, url: str, output_dir: Path) -> LighthouseData:
        """
        Run Lighthouse audits for mobile and desktop.
        """
        mobile_result = self._run_lighthouse(url, output_dir, "mobile")
        desktop_result = self._run_lighthouse(url, output_dir, "desktop")
        
        return LighthouseData(
            url=url,
            mobile=mobile_result,
            desktop=desktop_result,
            mobile_cwv=self._extract_cwv(mobile_result),
            desktop_cwv=self._extract_cwv(desktop_result),
            opportunities=self._extract_opportunities(mobile_result),
        )
    
    def _run_lighthouse(
        self,
        url: str,
        output_dir: Path,
        mode: str,  # "mobile" or "desktop"
    ) -> Dict[str, Any]:
        """
        Run Lighthouse CLI and return JSON result.
        """
        output_path = output_dir / f"lighthouse_{mode}.json"
        
        cmd = [
            "lighthouse",
            url,
            "--output=json",
            f"--output-path={output_path}",
            "--chrome-flags=--headless --no-sandbox",
            "--quiet",
        ]
        
        if mode == "desktop":
            cmd.append("--preset=desktop")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode != 0:
                logger.warning(f"Lighthouse {mode} warning: {result.stderr}")
            
            if output_path.exists():
                with open(output_path) as f:
                    return json.load(f)
            else:
                raise LighthouseError(f"Lighthouse output not found: {output_path}")
                
        except subprocess.TimeoutExpired:
            raise LighthouseError(f"Lighthouse {mode} audit timed out")
        except Exception as e:
            raise LighthouseError(f"Lighthouse {mode} failed: {e}")
    
    def _extract_cwv(self, result: Dict) -> CoreWebVitals:
        """Extract Core Web Vitals from Lighthouse result."""
        audits = result.get("audits", {})
        
        return CoreWebVitals(
            lcp=self._get_metric(audits, "largest-contentful-paint"),
            fid=self._get_metric(audits, "max-potential-fid"),
            cls=self._get_metric(audits, "cumulative-layout-shift"),
            inp=self._get_metric(audits, "experimental-interaction-to-next-paint"),
            ttfb=self._get_metric(audits, "server-response-time"),
            tbt=self._get_metric(audits, "total-blocking-time"),
            fcp=self._get_metric(audits, "first-contentful-paint"),
            si=self._get_metric(audits, "speed-index"),
        )
    
    def _get_metric(self, audits: Dict, key: str) -> Optional[float]:
        """Get metric value from audits."""
        audit = audits.get(key, {})
        return audit.get("numericValue")
    
    def _extract_opportunities(self, result: Dict) -> list[LighthouseOpportunity]:
        """Extract optimization opportunities."""
        opportunities = []
        audits = result.get("audits", {})
        
        opportunity_keys = [
            "render-blocking-resources",
            "unused-css-rules",
            "unused-javascript",
            "modern-image-formats",
            "uses-optimized-images",
            "uses-responsive-images",
            "efficient-animated-content",
            "uses-text-compression",
            "uses-rel-preconnect",
            "server-response-time",
            "redirects",
            "uses-long-cache-ttl",
            "total-byte-weight",
            "dom-size",
            "font-display",
        ]
        
        for key in opportunity_keys:
            audit = audits.get(key, {})
            if audit.get("score", 1) < 1:  # Has room for improvement
                details = audit.get("details", {})
                savings = details.get("overallSavingsMs", 0)
                
                opportunities.append(LighthouseOpportunity(
                    id=key,
                    title=audit.get("title", key),
                    description=audit.get("description", ""),
                    score=audit.get("score", 0),
                    savings_ms=savings,
                    display_value=audit.get("displayValue", ""),
                ))
        
        # Sort by potential savings
        opportunities.sort(key=lambda x: x.savings_ms or 0, reverse=True)
        
        return opportunities[:10]  # Top 10 opportunities
```

### 4. HTTP Probe Module (`proofkit/collector/http_probe.py`)

```python
import httpx
import ssl
from typing import Dict, List, Optional
from urllib.parse import urlparse

from proofkit.utils.logger import logger
from .models import HttpProbeData, SecurityHeaders, SSLInfo, RedirectChain


class HttpProbeCollector:
    """
    HTTP-level probing for headers, SSL, redirects, security.
    """
    
    SECURITY_HEADERS = [
        "strict-transport-security",
        "content-security-policy",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
        "x-xss-protection",
    ]
    
    def collect(self, url: str) -> HttpProbeData:
        """
        Probe URL for HTTP-level information.
        """
        redirect_chain = self._follow_redirects(url)
        final_url = redirect_chain[-1] if redirect_chain else url
        
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            response = client.get(url)
            
            return HttpProbeData(
                url=url,
                final_url=str(response.url),
                status_code=response.status_code,
                redirect_chain=redirect_chain,
                response_time_ms=response.elapsed.total_seconds() * 1000,
                headers=dict(response.headers),
                security_headers=self._check_security_headers(response.headers),
                ssl_info=self._check_ssl(url),
                server=response.headers.get("server"),
                robots_txt=self._fetch_robots(url),
                sitemap_exists=self._check_sitemap(url),
            )
    
    def _follow_redirects(self, url: str) -> List[str]:
        """Track redirect chain."""
        chain = []
        current_url = url
        
        with httpx.Client(follow_redirects=False, timeout=10) as client:
            for _ in range(10):  # Max 10 redirects
                try:
                    response = client.head(current_url)
                    chain.append(current_url)
                    
                    if response.status_code in (301, 302, 303, 307, 308):
                        current_url = response.headers.get("location", "")
                        if not current_url.startswith("http"):
                            # Relative URL
                            parsed = urlparse(chain[-1])
                            current_url = f"{parsed.scheme}://{parsed.netloc}{current_url}"
                    else:
                        break
                except Exception:
                    break
        
        return chain
    
    def _check_security_headers(self, headers) -> SecurityHeaders:
        """Check presence and values of security headers."""
        present = {}
        missing = []
        
        for header in self.SECURITY_HEADERS:
            value = headers.get(header)
            if value:
                present[header] = value
            else:
                missing.append(header)
        
        return SecurityHeaders(
            present=present,
            missing=missing,
            has_hsts="strict-transport-security" in present,
            has_csp="content-security-policy" in present,
            has_xframe="x-frame-options" in present,
            score=len(present) / len(self.SECURITY_HEADERS) * 100,
        )
    
    def _check_ssl(self, url: str) -> Optional[SSLInfo]:
        """Check SSL certificate information."""
        if not url.startswith("https"):
            return SSLInfo(valid=False, error="Not using HTTPS")
        
        try:
            parsed = urlparse(url)
            hostname = parsed.netloc
            
            context = ssl.create_default_context()
            with context.wrap_socket(
                ssl.socket.socket(), 
                server_hostname=hostname
            ) as sock:
                sock.connect((hostname, 443))
                cert = sock.getpeercert()
                
                return SSLInfo(
                    valid=True,
                    issuer=dict(x[0] for x in cert.get("issuer", [])).get("organizationName"),
                    expires=cert.get("notAfter"),
                    subject=dict(x[0] for x in cert.get("subject", [])).get("commonName"),
                )
        except Exception as e:
            return SSLInfo(valid=False, error=str(e))
    
    def _fetch_robots(self, url: str) -> Optional[str]:
        """Fetch robots.txt content."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            response = httpx.get(robots_url, timeout=10)
            if response.status_code == 200:
                return response.text[:2000]  # Limit size
        except Exception:
            pass
        
        return None
    
    def _check_sitemap(self, url: str) -> bool:
        """Check if sitemap.xml exists."""
        parsed = urlparse(url)
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
        
        try:
            response = httpx.head(sitemap_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
```

### 5. Collector Models (`proofkit/collector/models.py`)

```python
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from proofkit.schemas.audit import AuditMode


class CTAInfo(BaseModel):
    text: str
    type: str  # "link" or "button"
    href: Optional[str] = None
    is_visible: bool = True
    is_above_fold: bool = False
    selector: Optional[str] = None


class FormInfo(BaseModel):
    action: Optional[str] = None
    method: str = "GET"
    field_count: int = 0
    required_count: int = 0
    has_email_field: bool = False
    has_phone_field: bool = False
    submit_button_text: str = "Submit"


class NavigationInfo(BaseModel):
    links: List[Dict[str, str]] = []
    has_hamburger: bool = False
    depth: int = 1


class PageSnapshot(BaseModel):
    url: str
    title: str
    headings: Dict[str, List[str]]
    ctas: List[CTAInfo] = []
    mobile_ctas: List[CTAInfo] = []
    forms: List[FormInfo] = []
    navigation: NavigationInfo
    whatsapp_links: List[Dict] = []
    contact_info: Dict = {}
    screenshots: List[str] = []
    hamburger_menu_works: Optional[bool] = None
    console_errors: List[str] = []


class SnapshotData(BaseModel):
    url: str
    pages: List[PageSnapshot]
    screenshots: List[str]
    total_ctas: int
    total_forms: int


class CoreWebVitals(BaseModel):
    lcp: Optional[float] = None  # Largest Contentful Paint (ms)
    fid: Optional[float] = None  # First Input Delay (ms)
    cls: Optional[float] = None  # Cumulative Layout Shift
    inp: Optional[float] = None  # Interaction to Next Paint (ms)
    ttfb: Optional[float] = None  # Time to First Byte (ms)
    tbt: Optional[float] = None  # Total Blocking Time (ms)
    fcp: Optional[float] = None  # First Contentful Paint (ms)
    si: Optional[float] = None   # Speed Index


class LighthouseOpportunity(BaseModel):
    id: str
    title: str
    description: str
    score: float
    savings_ms: Optional[float] = None
    display_value: str = ""


class LighthouseData(BaseModel):
    url: str
    mobile: Dict[str, Any]
    desktop: Dict[str, Any]
    mobile_cwv: CoreWebVitals
    desktop_cwv: CoreWebVitals
    opportunities: List[LighthouseOpportunity] = []


class SecurityHeaders(BaseModel):
    present: Dict[str, str] = {}
    missing: List[str] = []
    has_hsts: bool = False
    has_csp: bool = False
    has_xframe: bool = False
    score: float = 0


class SSLInfo(BaseModel):
    valid: bool
    issuer: Optional[str] = None
    expires: Optional[str] = None
    subject: Optional[str] = None
    error: Optional[str] = None


class HttpProbeData(BaseModel):
    url: str
    final_url: str
    status_code: int
    redirect_chain: List[str] = []
    response_time_ms: float
    headers: Dict[str, str] = {}
    security_headers: SecurityHeaders
    ssl_info: Optional[SSLInfo] = None
    server: Optional[str] = None
    robots_txt: Optional[str] = None
    sitemap_exists: bool = False


class RawData(BaseModel):
    """Complete raw data from all collectors."""
    url: str
    mode: AuditMode
    pages_audited: List[str]
    snapshot: SnapshotData
    lighthouse: LighthouseData
    http_probe: HttpProbeData
    detected_stack: Dict[str, Any] = {}
    business_signals: Dict[str, Any] = {}
```

## Testing Requirements

```python
# tests/collector/test_playwright.py
# tests/collector/test_lighthouse.py
# tests/collector/test_http_probe.py
# tests/collector/conftest.py - fixtures with mock responses
```

## Your First Tasks (Phase 1 MVP)

1. [ ] Create `proofkit/collector/__init__.py` with Collector class
2. [ ] Implement `models.py` with all data classes
3. [ ] Implement `playwright_snapshot.py` - core DOM extraction
4. [ ] Implement `lighthouse.py` - CLI wrapper
5. [ ] Implement `http_probe.py` - header/SSL checks
6. [ ] Add `stack_detector.py` - basic CMS/framework detection
7. [ ] Add `business_detector.py` - keyword-based business type detection
8. [ ] Write tests for each module
9. [ ] Test on 3+ real websites
