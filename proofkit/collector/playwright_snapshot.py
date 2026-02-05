"""Playwright-based browser data collection."""

import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, urljoin

from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import PlaywrightError, PlaywrightTimeoutError

from .models import (
    SnapshotData,
    PageSnapshot,
    CTAInfo,
    FormInfo,
    NavigationInfo,
)


# Detection patterns
WHATSAPP_PATTERNS = [
    r"wa\.me\/",
    r"api\.whatsapp\.com\/send",
    r"whatsapp:\/\/send",
    r"web\.whatsapp\.com",
]

CTA_KEYWORDS = [
    "contact", "call", "whatsapp", "book", "get quote", "get a quote",
    "inquire", "enquire", "submit", "request", "buy", "shop", "order",
    "schedule", "start", "try", "demo", "free trial", "sign up", "register",
    "subscribe", "download", "learn more", "get started", "apply now",
]

PRIORITY_PAGES = [
    "contact", "about", "services", "products", "pricing", "property",
    "portfolio", "gallery", "menu", "rooms", "booking", "shop", "store",
]


class PlaywrightCollector:
    """Browser-based data collection using Playwright."""

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

        Args:
            url: Base URL being audited
            pages: List of page URLs to snapshot
            output_dir: Directory for screenshots

        Returns:
            SnapshotData containing all collected information
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise PlaywrightError("Playwright not installed. Run: pip install playwright && playwright install")

        page_snapshots = []
        screenshots = []

        screenshots_dir = output_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for page_url in pages:
                try:
                    logger.info(f"Snapshotting {page_url}")
                    snapshot = self._snapshot_page(browser, page_url, screenshots_dir)
                    page_snapshots.append(snapshot)
                    screenshots.extend(snapshot.screenshots)
                except Exception as e:
                    logger.warning(f"Failed to snapshot {page_url}: {e}")
                    # Add minimal snapshot with error
                    page_snapshots.append(PageSnapshot(
                        url=page_url,
                        console_errors=[str(e)],
                    ))

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
        browser,
        url: str,
        output_dir: Path,
    ) -> PageSnapshot:
        """Snapshot a single page with desktop and mobile viewports."""
        console_errors = []

        # Desktop viewport
        desktop_page = browser.new_page(viewport={"width": 1440, "height": 900})

        # Capture console errors
        desktop_page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        try:
            desktop_page.goto(url, wait_until="networkidle", timeout=self.timeout)
        except Exception as e:
            if "timeout" in str(e).lower():
                raise PlaywrightTimeoutError(f"Page load timeout: {url}")
            raise PlaywrightError(f"Failed to load page: {e}")

        # Scroll to trigger lazy content
        self._scroll_page(desktop_page)

        # Extract data from desktop
        title = self._get_title(desktop_page)
        headings = self._get_headings(desktop_page)
        meta_tags = self._get_meta_tags(desktop_page)
        ctas = self._get_ctas(desktop_page)
        forms = self._get_forms(desktop_page)
        navigation = self._get_navigation(desktop_page)
        whatsapp_links = self._get_whatsapp_links(desktop_page)
        contact_info = self._get_contact_info(desktop_page)

        # Take desktop screenshot
        page_name = self._url_to_filename(url)
        desktop_screenshot = output_dir / f"{page_name}_desktop.png"
        desktop_page.screenshot(path=str(desktop_screenshot), full_page=True)

        # Mobile viewport
        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})

        try:
            mobile_page.goto(url, wait_until="networkidle", timeout=self.timeout)
            self._scroll_page(mobile_page)

            # Take mobile screenshot
            mobile_screenshot = output_dir / f"{page_name}_mobile.png"
            mobile_page.screenshot(path=str(mobile_screenshot), full_page=True)

            # Mobile-specific data
            mobile_ctas = self._get_ctas(mobile_page)
            hamburger_works = self._test_hamburger_menu(mobile_page)
        except Exception as e:
            logger.warning(f"Mobile snapshot failed: {e}")
            mobile_screenshot = None
            mobile_ctas = []
            hamburger_works = None

        desktop_page.close()
        mobile_page.close()

        screenshots = [str(desktop_screenshot)]
        if mobile_screenshot:
            screenshots.append(str(mobile_screenshot))

        return PageSnapshot(
            url=url,
            title=title,
            headings=headings,
            meta_tags=meta_tags,
            ctas=ctas,
            mobile_ctas=mobile_ctas,
            forms=forms,
            navigation=navigation,
            whatsapp_links=whatsapp_links,
            contact_info=contact_info,
            screenshots=screenshots,
            hamburger_menu_works=hamburger_works,
            console_errors=console_errors[:10],  # Limit errors
        )

    def _scroll_page(self, page, scrolls: int = 3):
        """Scroll page to trigger lazy loading."""
        for _ in range(scrolls):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(300)

    def _get_title(self, page) -> str:
        """Get page title."""
        try:
            return page.title().strip()
        except Exception:
            return ""

    def _get_headings(self, page) -> Dict[str, List[str]]:
        """Extract H1-H3 headings."""
        headings = {"h1": [], "h2": [], "h3": []}

        for level in ["h1", "h2", "h3"]:
            try:
                texts = page.locator(level).all_inner_texts()
                headings[level] = [h.strip() for h in texts if h.strip()][:10]
            except Exception:
                continue

        return headings

    def _get_meta_tags(self, page) -> Dict[str, str]:
        """Extract important meta tags."""
        meta_tags = {}

        try:
            # Description
            desc = page.locator('meta[name="description"]').get_attribute("content")
            if desc:
                meta_tags["description"] = desc

            # Keywords
            keywords = page.locator('meta[name="keywords"]').get_attribute("content")
            if keywords:
                meta_tags["keywords"] = keywords

            # OG tags
            og_title = page.locator('meta[property="og:title"]').get_attribute("content")
            if og_title:
                meta_tags["og:title"] = og_title

            og_desc = page.locator('meta[property="og:description"]').get_attribute("content")
            if og_desc:
                meta_tags["og:description"] = og_desc

            # Viewport
            viewport = page.locator('meta[name="viewport"]').get_attribute("content")
            if viewport:
                meta_tags["viewport"] = viewport

            # Canonical
            canonical = page.locator('link[rel="canonical"]').get_attribute("href")
            if canonical:
                meta_tags["canonical"] = canonical

        except Exception:
            pass

        return meta_tags

    def _get_ctas(self, page) -> List[CTAInfo]:
        """Extract CTA buttons and links."""
        ctas = []

        # Check links
        try:
            links = page.locator("a").all()
            for link in links[:100]:  # Limit to avoid performance issues
                try:
                    text = (link.inner_text() or "").strip().lower()
                    href = link.get_attribute("href") or ""

                    if any(kw in text for kw in CTA_KEYWORDS):
                        bbox = link.bounding_box()
                        ctas.append(CTAInfo(
                            text=text[:100],
                            type="link",
                            href=href[:500] if href else None,
                            is_visible=link.is_visible(),
                            is_above_fold=bbox["y"] < 900 if bbox else False,
                            selector=self._get_selector(link),
                        ))
                except Exception:
                    continue
        except Exception:
            pass

        # Check buttons
        try:
            buttons = page.locator("button").all()
            for button in buttons[:50]:
                try:
                    text = (button.inner_text() or "").strip().lower()

                    if any(kw in text for kw in CTA_KEYWORDS) or not text:
                        bbox = button.bounding_box()
                        ctas.append(CTAInfo(
                            text=text[:100] if text else "[button]",
                            type="button",
                            href=None,
                            is_visible=button.is_visible(),
                            is_above_fold=bbox["y"] < 900 if bbox else False,
                            selector=self._get_selector(button),
                        ))
                except Exception:
                    continue
        except Exception:
            pass

        return ctas[:30]  # Limit to avoid huge lists

    def _get_whatsapp_links(self, page) -> List[Dict[str, Any]]:
        """Find WhatsApp contact options."""
        whatsapp_links = []

        try:
            links = page.locator("a").all()
            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    text = (link.inner_text() or "").strip()

                    is_whatsapp = (
                        any(re.search(p, href, re.IGNORECASE) for p in WHATSAPP_PATTERNS)
                        or "whatsapp" in text.lower()
                        or "whatsapp" in href.lower()
                    )

                    if is_whatsapp:
                        bbox = link.bounding_box()
                        whatsapp_links.append({
                            "text": text[:100],
                            "href": href[:500],
                            "is_visible": link.is_visible(),
                            "is_above_fold": bbox["y"] < 900 if bbox else False,
                        })
                except Exception:
                    continue
        except Exception:
            pass

        return whatsapp_links[:10]

    def _get_forms(self, page) -> List[FormInfo]:
        """Analyze forms on the page."""
        forms = []

        try:
            form_elements = page.locator("form").all()
            for form in form_elements[:10]:
                try:
                    inputs = form.locator("input, textarea, select").all()
                    required_count = 0
                    has_email = False
                    has_phone = False

                    for inp in inputs:
                        try:
                            if inp.get_attribute("required") is not None:
                                required_count += 1

                            inp_type = inp.get_attribute("type") or ""
                            inp_name = (inp.get_attribute("name") or "").lower()

                            if inp_type == "email" or "email" in inp_name:
                                has_email = True
                            if inp_type == "tel" or "phone" in inp_name or "mobile" in inp_name:
                                has_phone = True
                        except Exception:
                            continue

                    forms.append(FormInfo(
                        action=form.get_attribute("action"),
                        method=(form.get_attribute("method") or "GET").upper(),
                        field_count=len(inputs),
                        required_count=required_count,
                        has_email_field=has_email,
                        has_phone_field=has_phone,
                        submit_button_text=self._get_submit_button_text(form),
                    ))
                except Exception:
                    continue
        except Exception:
            pass

        return forms

    def _get_navigation(self, page) -> NavigationInfo:
        """Extract navigation structure."""
        nav_links = []

        # Try common nav selectors
        for selector in ["nav a", "header a", "[role='navigation'] a", ".nav a", ".navbar a"]:
            try:
                links = page.locator(selector).all()
                if links:
                    for link in links[:20]:
                        try:
                            text = (link.inner_text() or "").strip()
                            href = link.get_attribute("href") or ""
                            if text and href and len(text) < 50:
                                nav_links.append({"text": text, "href": href})
                        except Exception:
                            continue
                    if nav_links:
                        break
            except Exception:
                continue

        # Check for hamburger menu
        has_hamburger = False
        try:
            hamburger_selectors = [
                "[class*='hamburger']",
                "[class*='mobile-menu']",
                "[class*='menu-toggle']",
                "button[aria-label*='menu']",
                ".navbar-toggler",
            ]
            for sel in hamburger_selectors:
                if page.locator(sel).count() > 0:
                    has_hamburger = True
                    break
        except Exception:
            pass

        return NavigationInfo(
            links=nav_links,
            has_hamburger=has_hamburger,
            depth=min(3, len(nav_links) // 5 + 1) if nav_links else 1,
        )

    def _get_contact_info(self, page) -> Dict[str, Any]:
        """Extract contact information."""
        contact = {
            "phones": [],
            "emails": [],
            "has_tel_link": False,
            "has_mailto_link": False,
        }

        try:
            html = page.content()

            # Phone patterns (basic)
            phone_pattern = r'(?:\+?[\d\s\-().]{10,20})'
            phones = re.findall(phone_pattern, html)
            contact["phones"] = list(set(p.strip() for p in phones if len(p.strip()) >= 10))[:5]

            # Email patterns
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, html)
            contact["emails"] = list(set(emails))[:5]

            # Check for tel: and mailto: links
            contact["has_tel_link"] = 'href="tel:' in html or "href='tel:" in html
            contact["has_mailto_link"] = 'href="mailto:' in html or "href='mailto:" in html

        except Exception:
            pass

        return contact

    def _test_hamburger_menu(self, page) -> Optional[bool]:
        """Test if hamburger menu works on mobile."""
        hamburger_selectors = [
            "[class*='hamburger']",
            "[class*='mobile-menu']",
            "[class*='menu-toggle']",
            "button[aria-label*='menu']",
            ".navbar-toggler",
        ]

        for sel in hamburger_selectors:
            try:
                hamburger = page.locator(sel).first
                if hamburger.is_visible():
                    hamburger.click()
                    page.wait_for_timeout(500)

                    # Check if nav appeared
                    nav_visible = page.locator("nav, [role='navigation'], .nav-menu, .mobile-nav").first.is_visible()
                    return nav_visible
            except Exception:
                continue

        return None

    def _get_selector(self, element) -> str:
        """Generate a selector for an element."""
        try:
            return element.evaluate(
                "el => el.tagName.toLowerCase() + "
                "(el.id ? '#' + el.id : '') + "
                "(el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '')"
            )
        except Exception:
            return ""

    def _get_submit_button_text(self, form) -> str:
        """Get text of form's submit button."""
        try:
            submit = form.locator("button[type='submit'], input[type='submit']").first
            text = submit.inner_text() or submit.get_attribute("value") or "Submit"
            return text.strip()[:50]
        except Exception:
            return "Submit"

    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename."""
        # Remove protocol and clean
        clean = url.split("//")[-1]
        clean = re.sub(r'[^\w\-]', '_', clean)
        return clean[:50]

    def discover_key_pages(self, url: str, max_pages: int = 5) -> List[str]:
        """Discover key pages from navigation."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return [url]

        pages = [url]
        base_domain = urlparse(url).netloc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(url, wait_until="networkidle", timeout=self.timeout)
                nav = self._get_navigation(page)

                for link in nav.links:
                    if len(pages) >= max_pages:
                        break

                    href = link.get("href", "")
                    text = link.get("text", "").lower()

                    # Make absolute URL
                    if href.startswith("/"):
                        href = urljoin(url, href)

                    # Check if internal and priority page
                    if href.startswith("http"):
                        link_domain = urlparse(href).netloc
                        if link_domain == base_domain:
                            is_priority = any(kw in text or kw in href.lower() for kw in PRIORITY_PAGES)
                            if is_priority and href not in pages:
                                pages.append(href)

            except Exception as e:
                logger.warning(f"Failed to discover pages: {e}")
            finally:
                browser.close()

        return pages

    def crawl_site(self, url: str, max_pages: int = 50) -> List[str]:
        """Full site crawl - discover all internal pages."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return [url]

        visited = set()
        to_visit = [url]
        pages = []
        base_domain = urlparse(url).netloc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            while to_visit and len(pages) < max_pages:
                current_url = to_visit.pop(0)

                if current_url in visited:
                    continue

                visited.add(current_url)

                try:
                    page.goto(current_url, wait_until="networkidle", timeout=self.timeout)
                    pages.append(current_url)

                    # Find all links
                    links = page.locator("a").all()
                    for link in links:
                        try:
                            href = link.get_attribute("href") or ""

                            if href.startswith("/"):
                                href = urljoin(current_url, href)

                            if href.startswith("http"):
                                link_domain = urlparse(href).netloc
                                if link_domain == base_domain and href not in visited:
                                    # Skip anchors, query params variations
                                    clean_href = href.split("#")[0].split("?")[0]
                                    if clean_href not in visited:
                                        to_visit.append(clean_href)
                        except Exception:
                            continue

                except Exception as e:
                    logger.warning(f"Failed to crawl {current_url}: {e}")

            browser.close()

        return pages
