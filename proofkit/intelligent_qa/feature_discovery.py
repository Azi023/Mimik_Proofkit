"""
Intelligent Feature Discovery

Automatically discovers all interactive elements on a web page
and categorizes them by type and expected behavior.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from playwright.async_api import Page, async_playwright

from proofkit.utils.logger import logger


class FeatureType(str, Enum):
    """Types of interactive features."""
    NAVIGATION = "navigation"
    FORM = "form"
    BUTTON = "button"
    LINK = "link"
    ACCORDION = "accordion"
    DROPDOWN = "dropdown"
    MODAL = "modal"
    CAROUSEL = "carousel"
    VIDEO = "video"
    MAP = "map"
    SOCIAL = "social"
    WHATSAPP = "whatsapp"
    CHAT = "chat"
    SEARCH = "search"
    GALLERY = "gallery"
    TAB = "tab"
    TOOLTIP = "tooltip"
    NOTIFICATION = "notification"
    COOKIE_BANNER = "cookie_banner"


@dataclass
class DiscoveredFeature:
    """Represents a discovered interactive feature."""
    id: str
    type: FeatureType
    element: str  # CSS selector or description
    location: str  # Page section (header, footer, main, etc.)
    text: str  # Visible text
    expected_behavior: str  # What should happen when interacted with
    attributes: Dict[str, Any] = field(default_factory=dict)
    test_cases: List[Dict[str, Any]] = field(default_factory=list)


class FeatureDiscovery:
    """
    Discovers all interactive features on a page.
    """

    # Patterns to identify feature types
    FEATURE_PATTERNS = {
        FeatureType.WHATSAPP: [
            "a[href*='wa.me']",
            "a[href*='whatsapp']",
            "[class*='whatsapp']",
            "[id*='whatsapp']",
        ],
        FeatureType.FORM: [
            "form",
            "[role='form']",
        ],
        FeatureType.NAVIGATION: [
            "nav",
            "[role='navigation']",
            "header nav",
            ".navbar",
            ".nav-menu",
        ],
        FeatureType.SEARCH: [
            "input[type='search']",
            "[role='search']",
            ".search-form",
            "#search",
        ],
        FeatureType.ACCORDION: [
            "[data-accordion]",
            ".accordion",
            "[role='tablist']",
            ".faq",
            ".collapse",
        ],
        FeatureType.DROPDOWN: [
            "select",
            "[role='listbox']",
            "[role='combobox']",
            ".dropdown",
        ],
        FeatureType.MODAL: [
            "[role='dialog']",
            ".modal",
            "[data-modal]",
        ],
        FeatureType.CAROUSEL: [
            ".carousel",
            ".slider",
            ".swiper",
            "[data-carousel]",
        ],
        FeatureType.GALLERY: [
            ".gallery",
            "[data-gallery]",
            ".lightbox",
        ],
        FeatureType.SOCIAL: [
            "a[href*='facebook.com']",
            "a[href*='twitter.com']",
            "a[href*='instagram.com']",
            "a[href*='linkedin.com']",
            "a[href*='youtube.com']",
        ],
        FeatureType.VIDEO: [
            "video",
            "iframe[src*='youtube']",
            "iframe[src*='vimeo']",
            ".video-player",
        ],
        FeatureType.MAP: [
            "iframe[src*='google.com/maps']",
            ".map",
            "[data-map]",
            "#map",
        ],
        FeatureType.CHAT: [
            "[class*='chat']",
            "[id*='chat']",
            "[class*='intercom']",
            "[class*='crisp']",
            "[class*='tawk']",
        ],
        FeatureType.COOKIE_BANNER: [
            "[class*='cookie']",
            "[id*='cookie']",
            "[class*='consent']",
            "[class*='gdpr']",
        ],
    }

    def __init__(self, page: Optional[Page] = None):
        self.page = page
        self.features: List[DiscoveredFeature] = []
        self.feature_count = 0

    async def discover_all(self, url: Optional[str] = None) -> List[DiscoveredFeature]:
        """
        Discover all interactive features on the page.

        Args:
            url: Optional URL to navigate to first

        Returns:
            List of discovered features
        """
        if url and self.page:
            await self.page.goto(url)
            await self.page.wait_for_load_state("networkidle")

        if not self.page:
            raise ValueError("No page available for discovery")

        logger.info(f"Starting feature discovery on {self.page.url}")

        # Discover by pattern
        for feature_type, selectors in self.FEATURE_PATTERNS.items():
            await self._discover_by_selectors(feature_type, selectors)

        # Discover generic buttons and links
        await self._discover_buttons()
        await self._discover_links()

        # Infer behaviors for each feature
        for feature in self.features:
            feature.expected_behavior = self._infer_behavior(feature)
            feature.test_cases = self._generate_test_cases(feature)

        logger.info(f"Discovered {len(self.features)} interactive features")
        return self.features

    async def _discover_by_selectors(
        self,
        feature_type: FeatureType,
        selectors: List[str]
    ):
        """Discover features by CSS selectors."""
        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    await self._add_feature(element, feature_type)
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

    async def _discover_buttons(self):
        """Discover all button elements."""
        selectors = [
            "button",
            "[role='button']",
            "input[type='submit']",
            "input[type='button']",
            ".btn",
            ".button",
            "a.cta",
        ]

        for selector in selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    if not await self._is_already_discovered(element):
                        await self._add_feature(element, FeatureType.BUTTON)
            except Exception:
                continue

    async def _discover_links(self):
        """Discover all link elements."""
        try:
            links = await self.page.query_selector_all("a[href]")
            for link in links:
                if not await self._is_already_discovered(link):
                    href = await link.get_attribute("href") or ""
                    # Skip anchor links and already-discovered
                    if href and not href.startswith("#"):
                        await self._add_feature(link, FeatureType.LINK)
        except Exception:
            pass

    async def _add_feature(self, element, feature_type: FeatureType):
        """Add a discovered feature."""
        self.feature_count += 1

        try:
            text = await element.inner_text()
            text = text.strip()[:100] if text else ""
        except Exception:
            text = ""

        try:
            location = await self._get_element_location(element)
        except Exception:
            location = "unknown"

        try:
            tag = await element.evaluate("el => el.tagName.toLowerCase()")
            class_name = await element.get_attribute("class") or ""
            element_id = await element.get_attribute("id") or ""
        except Exception:
            tag = "unknown"
            class_name = ""
            element_id = ""

        # Build selector
        selector_parts = [tag]
        if element_id:
            selector_parts.append(f"#{element_id}")
        elif class_name:
            first_class = class_name.split()[0] if class_name else ""
            if first_class:
                selector_parts.append(f".{first_class}")

        feature = DiscoveredFeature(
            id=f"feat_{self.feature_count:04d}",
            type=feature_type,
            element="".join(selector_parts),
            location=location,
            text=text,
            expected_behavior="",  # Will be inferred
            attributes={
                "tag": tag,
                "class": class_name,
                "id": element_id,
            },
        )

        self.features.append(feature)

    async def _get_element_location(self, element) -> str:
        """Determine where the element is on the page."""
        try:
            # Check if in header
            in_header = await element.evaluate(
                "el => !!el.closest('header, .header, [role=\"banner\"]')"
            )
            if in_header:
                return "Header"

            # Check if in footer
            in_footer = await element.evaluate(
                "el => !!el.closest('footer, .footer, [role=\"contentinfo\"]')"
            )
            if in_footer:
                return "Footer"

            # Check if in nav
            in_nav = await element.evaluate(
                "el => !!el.closest('nav, .nav, [role=\"navigation\"]')"
            )
            if in_nav:
                return "Navigation"

            # Check if in sidebar
            in_sidebar = await element.evaluate(
                "el => !!el.closest('aside, .sidebar, [role=\"complementary\"]')"
            )
            if in_sidebar:
                return "Sidebar"

            # Check position on page
            box = await element.bounding_box()
            if box:
                viewport_height = await self.page.evaluate("window.innerHeight")
                if box["y"] < viewport_height:
                    return "Above the fold"
                return "Below the fold"

            return "Main content"

        except Exception:
            return "Unknown"

    async def _is_already_discovered(self, element) -> bool:
        """Check if element is already in discovered features."""
        try:
            element_id = await element.get_attribute("id")
            if element_id:
                for f in self.features:
                    if f.attributes.get("id") == element_id:
                        return True
        except Exception:
            pass
        return False

    def _infer_behavior(self, feature: DiscoveredFeature) -> str:
        """Infer expected behavior based on feature type and attributes."""
        behaviors = {
            FeatureType.WHATSAPP: "Should open WhatsApp chat with pre-filled message",
            FeatureType.FORM: "Should validate inputs and submit data to server",
            FeatureType.NAVIGATION: "Should navigate to linked pages",
            FeatureType.SEARCH: "Should filter/search content based on query",
            FeatureType.ACCORDION: "Should expand/collapse content sections",
            FeatureType.DROPDOWN: "Should show options and allow selection",
            FeatureType.MODAL: "Should open dialog overlay",
            FeatureType.CAROUSEL: "Should cycle through slides",
            FeatureType.GALLERY: "Should display images with lightbox",
            FeatureType.SOCIAL: "Should open social media profile in new tab",
            FeatureType.VIDEO: "Should play video content",
            FeatureType.MAP: "Should display interactive map",
            FeatureType.CHAT: "Should open live chat widget",
            FeatureType.COOKIE_BANNER: "Should allow accept/reject cookies",
            FeatureType.BUTTON: f"Should perform action: {feature.text or 'click action'}",
            FeatureType.LINK: "Should navigate to destination URL",
        }

        return behaviors.get(feature.type, "Unknown behavior")

    def _generate_test_cases(self, feature: DiscoveredFeature) -> List[Dict[str, Any]]:
        """Generate test cases for a feature."""
        test_cases = []

        if feature.type == FeatureType.WHATSAPP:
            test_cases = [
                {"name": "Click opens WhatsApp", "action": "click", "expected": "Opens wa.me link"},
                {"name": "Phone number format", "action": "verify", "expected": "Valid phone number"},
                {"name": "Opens in new tab", "action": "verify", "expected": "target=_blank"},
            ]

        elif feature.type == FeatureType.FORM:
            test_cases = [
                {"name": "Required field validation", "action": "submit_empty", "expected": "Shows validation error"},
                {"name": "Valid submission", "action": "submit_valid", "expected": "Success message or redirect"},
                {"name": "Error display", "action": "submit_invalid", "expected": "Shows appropriate error"},
            ]

        elif feature.type == FeatureType.NAVIGATION:
            test_cases = [
                {"name": "All links clickable", "action": "click_all", "expected": "No broken links"},
                {"name": "Current page indicator", "action": "verify", "expected": "Active state shown"},
                {"name": "Mobile menu toggle", "action": "toggle_mobile", "expected": "Menu opens/closes"},
            ]

        elif feature.type == FeatureType.BUTTON:
            test_cases = [
                {"name": "Click triggers action", "action": "click", "expected": "Expected action occurs"},
                {"name": "Keyboard accessible", "action": "press_enter", "expected": "Same as click"},
                {"name": "Visual feedback", "action": "hover", "expected": "Hover state visible"},
            ]

        elif feature.type == FeatureType.ACCORDION:
            test_cases = [
                {"name": "Toggle open/close", "action": "click", "expected": "Content expands/collapses"},
                {"name": "Multiple open allowed", "action": "click_multiple", "expected": "Depends on design"},
                {"name": "Keyboard navigation", "action": "keyboard", "expected": "Arrow keys work"},
            ]

        elif feature.type == FeatureType.SOCIAL:
            test_cases = [
                {"name": "Link is valid", "action": "verify_href", "expected": "Valid social URL"},
                {"name": "Opens in new tab", "action": "verify", "expected": "target=_blank"},
            ]

        else:
            test_cases = [
                {"name": "Element visible", "action": "verify", "expected": "Element is visible"},
                {"name": "Interaction works", "action": "interact", "expected": "Expected behavior occurs"},
            ]

        return test_cases

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of discovered features."""
        by_type = {}
        by_location = {}

        for f in self.features:
            # Count by type
            type_key = f.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by location
            by_location[f.location] = by_location.get(f.location, 0) + 1

        return {
            "total_features": len(self.features),
            "by_type": by_type,
            "by_location": by_location,
            "test_cases_generated": sum(len(f.test_cases) for f in self.features),
        }


async def discover_features(url: str) -> List[DiscoveredFeature]:
    """
    Convenience function to discover features on a URL.

    Args:
        url: URL to analyze

    Returns:
        List of discovered features
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

            discovery = FeatureDiscovery(page)
            features = await discovery.discover_all()

            return features
        finally:
            await browser.close()
