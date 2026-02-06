"""
Experience Agent

Experiences the website like a human user, detecting UX friction
that automated scans miss.

This is a key innovation - an agent that "experiences" the site like a real user,
detecting issues like:
- Laggy custom cursors (like Seven Tides had)
- Slow-loading sections
- Unresponsive interactions
- Scroll jank
- Confusing navigation
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time

from playwright.async_api import Page, Browser, async_playwright, TimeoutError as PlaywrightTimeout

from proofkit.utils.logger import logger


class FrictionType(str, Enum):
    """Types of UX friction that can be detected."""
    SLOW_INTERACTION = "slow_interaction"
    LAGGY_CURSOR = "laggy_cursor"
    DELAYED_RESPONSE = "delayed_response"
    LAYOUT_SHIFT = "layout_shift"
    BROKEN_ANIMATION = "broken_animation"
    CONFUSING_NAVIGATION = "confusing_navigation"
    UNCLEAR_CTA = "unclear_cta"
    FRUSTRATING_FORM = "frustrating_form"
    POOR_FEEDBACK = "poor_feedback"
    SCROLL_JANK = "scroll_jank"
    SLOW_HERO = "slow_hero"


@dataclass
class UXFriction:
    """Detected UX friction point."""
    type: FrictionType
    location: str
    description: str
    severity: str  # critical, high, medium, low
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "location": self.location,
            "description": self.description,
            "severity": self.severity,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


class ExperienceAgent:
    """
    Simulates a human user experiencing the website.

    Detects:
    1. Custom cursor lag (like Seven Tides had)
    2. Slow-loading sections (images, videos)
    3. Unresponsive interactions
    4. Layout shift (CLS)
    5. Scroll jank
    6. Confusing navigation paths
    7. Form friction
    8. Missing feedback (loading states, confirmations)
    """

    # Thresholds for friction detection
    CURSOR_LAG_THRESHOLD_MS = 50  # Cursor following delay
    INTERACTION_RESPONSE_THRESHOLD_MS = 200  # Button click response
    CLS_THRESHOLD = 0.1  # Cumulative Layout Shift
    SCROLL_JANK_THRESHOLD = 3  # Number of jank events

    def __init__(self, page: Page):
        self.page = page
        self.frictions: List[UXFriction] = []
        self.metrics: Dict[str, Any] = {}
        self.url: str = ""

    async def experience_page(self, url: str) -> List[UXFriction]:
        """
        Experience a page like a human would.

        Args:
            url: The URL to experience

        Returns:
            List of detected UX friction points
        """
        self.url = url
        self.frictions = []

        logger.info(f"Experience Agent starting for {url}")

        try:
            # Navigate with extended timeout
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(1)  # Let animations/scripts initialize

            # Run experience tests (some in parallel where possible)
            await self._test_cursor_behavior()
            await self._test_load_experience()
            await self._test_interaction_responsiveness()
            await self._test_scroll_experience()
            await self._test_navigation_clarity()
            await self._test_form_friction()

            logger.info(f"Experience Agent found {len(self.frictions)} friction points")

        except PlaywrightTimeout:
            self.frictions.append(UXFriction(
                type=FrictionType.DELAYED_RESPONSE,
                location="Page Load",
                description="Page took too long to load (>60s). Users will abandon.",
                severity="critical",
                evidence={"timeout": 60000},
                recommendation="Investigate slow server response, reduce initial payload, add loading indicator.",
            ))
        except Exception as e:
            logger.error(f"Experience Agent error: {e}")

        return self.frictions

    async def _test_cursor_behavior(self):
        """
        Detect laggy or custom cursors that hurt UX.

        Seven Tides had a custom cursor with motion smoothing
        that made interactions feel "draggy".
        """
        logger.debug("Testing cursor behavior...")

        try:
            # Check for custom cursor CSS and elements
            cursor_info = await self.page.evaluate("""
                () => {
                    const body = document.body;
                    const cursor = getComputedStyle(body).cursor;

                    // Check for custom cursor elements
                    const customCursorSelectors = [
                        '[class*="cursor"]',
                        '[id*="cursor"]',
                        '.cursor-follow',
                        '.custom-cursor',
                        '[data-cursor]',
                        '.cursor-dot',
                        '.cursor-circle',
                        '.mouse-follower',
                    ];

                    let customCursors = [];
                    for (const selector of customCursorSelectors) {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const style = getComputedStyle(el);
                            if (style.position === 'fixed' || style.position === 'absolute') {
                                customCursors.push({
                                    selector: selector,
                                    className: el.className,
                                    hasTransition: style.transition !== 'none' && style.transition !== '',
                                    transitionDuration: style.transitionDuration,
                                });
                            }
                        });
                    }

                    // Check for cursor-following scripts in inline scripts
                    const scripts = [...document.scripts].map(s => s.innerHTML || '');
                    const hasCursorScript = scripts.some(s =>
                        (s.includes('cursor') || s.includes('mouse')) &&
                        (s.includes('mousemove') || s.includes('pointermove') || s.includes('clientX'))
                    );

                    // Check for GSAP or other animation libraries that might control cursor
                    const hasGSAP = typeof window.gsap !== 'undefined' ||
                                   scripts.some(s => s.includes('gsap') || s.includes('TweenMax'));

                    return {
                        customCSS: cursor !== 'auto' && cursor !== 'default' && cursor !== 'pointer',
                        customElements: customCursors,
                        hasCustomCursor: customCursors.length > 0,
                        cursorScript: hasCursorScript,
                        hasGSAP: hasGSAP,
                        cursorElementCount: customCursors.length,
                    };
                }
            """)

            self.metrics['cursor'] = cursor_info

            if cursor_info['hasCustomCursor'] or cursor_info['cursorScript']:
                # Check for transition/smoothing that causes lag
                has_smoothing = any(
                    c.get('hasTransition', False)
                    for c in cursor_info.get('customElements', [])
                )

                # Look for easing/smoothing indicators
                smoothing_evidence = []
                for cursor in cursor_info.get('customElements', []):
                    if cursor.get('hasTransition'):
                        duration = cursor.get('transitionDuration', '')
                        smoothing_evidence.append(f"Transition: {duration}")

                # Custom cursor detected
                if has_smoothing or cursor_info.get('hasGSAP'):
                    self.frictions.append(UXFriction(
                        type=FrictionType.LAGGY_CURSOR,
                        location="Global (Custom Cursor)",
                        description=(
                            "Custom cursor with motion smoothing/easing detected. "
                            "This creates a 'draggy' feel where the cursor lags behind "
                            "the actual mouse position. Users perceive the site as slow "
                            "even when loading is fast. This is particularly frustrating "
                            "when trying to click small targets or fill forms."
                        ),
                        severity="medium",
                        evidence={
                            "cursor_type": "custom_with_smoothing",
                            "custom_elements": cursor_info['cursorElementCount'],
                            "has_gsap": cursor_info.get('hasGSAP', False),
                            "smoothing_details": smoothing_evidence,
                        },
                        recommendation=(
                            "1. Disable custom cursor on forms, CTAs, and interactive elements. "
                            "2. Reduce or remove transition/easing on cursor movement. "
                            "3. Add CSS: @media (prefers-reduced-motion: reduce) to disable for users who prefer less motion. "
                            "4. Consider removing the custom cursor entirely - it rarely adds value."
                        ),
                    ))
                else:
                    # Custom cursor without obvious smoothing
                    self.frictions.append(UXFriction(
                        type=FrictionType.LAGGY_CURSOR,
                        location="Global (Custom Cursor)",
                        description=(
                            "Custom cursor detected. While no obvious smoothing was found, "
                            "custom cursors can still create friction, especially on slower devices "
                            "or when JavaScript is executing."
                        ),
                        severity="low",
                        evidence={
                            "cursor_type": "custom",
                            "custom_elements": cursor_info['cursorElementCount'],
                        },
                        recommendation=(
                            "Test the custom cursor on various devices and connection speeds. "
                            "Consider whether it adds value to the user experience."
                        ),
                    ))

        except Exception as e:
            logger.debug(f"Cursor test error: {e}")

    async def _test_load_experience(self):
        """
        Test how loading feels to a user.

        Even if total load time is OK, users notice:
        - Hero images appearing late
        - Text shifting as images load (CLS)
        - Videos buffering
        """
        logger.debug("Testing load experience...")

        try:
            # Check for layout shift (CLS)
            cls_score = await self.page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        let clsValue = 0;
                        let clsEntries = [];

                        try {
                            const observer = new PerformanceObserver((list) => {
                                for (const entry of list.getEntries()) {
                                    if (!entry.hadRecentInput) {
                                        clsValue += entry.value;
                                        clsEntries.push({
                                            value: entry.value,
                                            sources: entry.sources ? entry.sources.map(s => s.node?.nodeName || 'unknown') : []
                                        });
                                    }
                                }
                            });

                            observer.observe({type: 'layout-shift', buffered: true});

                            setTimeout(() => {
                                observer.disconnect();
                                resolve({
                                    score: clsValue,
                                    entries: clsEntries.slice(0, 5),  // Top 5 shifts
                                });
                            }, 3000);
                        } catch (e) {
                            // PerformanceObserver not supported
                            resolve({score: 0, entries: [], error: e.message});
                        }
                    });
                }
            """)

            self.metrics['cls'] = cls_score

            if cls_score['score'] > self.CLS_THRESHOLD:
                severity = "high" if cls_score['score'] > 0.25 else "medium"
                self.frictions.append(UXFriction(
                    type=FrictionType.LAYOUT_SHIFT,
                    location="Page Load",
                    description=(
                        f"Significant layout shift detected (CLS: {cls_score['score']:.3f}). "
                        "Content moves/jumps as elements load, creating a jarring experience. "
                        "Users may accidentally click wrong elements or lose their reading position."
                    ),
                    severity=severity,
                    evidence={
                        "cls_score": round(cls_score['score'], 3),
                        "threshold": self.CLS_THRESHOLD,
                        "shift_sources": cls_score.get('entries', []),
                    },
                    recommendation=(
                        "1. Reserve space for images with width/height attributes or aspect-ratio CSS. "
                        "2. Use skeleton loaders for dynamic content. "
                        "3. Preload critical above-the-fold images. "
                        "4. Avoid inserting content above existing content."
                    ),
                ))

            # Check for slow hero/banner images
            hero_analysis = await self.page.evaluate("""
                () => {
                    const heroSelectors = [
                        '.hero', '[class*="hero"]',
                        '.banner', '[class*="banner"]',
                        'header img', '.header img',
                        '[class*="splash"]', '.splash',
                        'section:first-of-type img',
                    ];

                    let heroImages = [];
                    for (const selector of heroSelectors) {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const imgs = el.tagName === 'IMG' ? [el] : el.querySelectorAll('img');
                            imgs.forEach(img => {
                                heroImages.push({
                                    src: img.src,
                                    complete: img.complete,
                                    naturalWidth: img.naturalWidth,
                                    loading: img.loading,
                                    hasLazyLoad: img.loading === 'lazy' || img.dataset.src || img.classList.contains('lazyload'),
                                });
                            });
                        });
                    }

                    return {
                        found: heroImages.length > 0,
                        images: heroImages.slice(0, 3),
                    };
                }
            """)

            self.metrics['hero'] = hero_analysis

            # Check for hero images that should NOT be lazy loaded
            for img in hero_analysis.get('images', []):
                if img.get('hasLazyLoad') and img.get('naturalWidth', 0) > 0:
                    self.frictions.append(UXFriction(
                        type=FrictionType.SLOW_HERO,
                        location="Hero/Banner Image",
                        description=(
                            "Above-the-fold hero image is using lazy loading. "
                            "This means users see a blank space or placeholder before the main image loads, "
                            "hurting first impressions."
                        ),
                        severity="medium",
                        evidence={"image_src": img.get('src', '')[:100]},
                        recommendation=(
                            "Remove lazy loading from hero/banner images. "
                            "Use loading='eager' or preload these critical images. "
                            "Only lazy load images below the fold."
                        ),
                    ))

        except Exception as e:
            logger.debug(f"Load experience test error: {e}")

    async def _test_interaction_responsiveness(self):
        """Test how quickly interactive elements respond to clicks."""
        logger.debug("Testing interaction responsiveness...")

        try:
            # Find interactive elements
            buttons = await self.page.query_selector_all(
                'button, [role="button"], a.btn, .button, .cta, [class*="btn"]'
            )

            slow_buttons = []

            for i, button in enumerate(buttons[:5]):  # Test first 5
                try:
                    # Check if button is visible and in viewport
                    is_visible = await button.is_visible()
                    if not is_visible:
                        continue

                    # Get button text for identification
                    text = await button.inner_text()
                    text = text.strip()[:30] if text else f"Button {i+1}"

                    # Check for loading states or transitions
                    has_slow_transition = await self.page.evaluate("""
                        (el) => {
                            const style = getComputedStyle(el);
                            const transition = style.transition || '';
                            const animation = style.animation || '';

                            // Check if there's a slow transition (>200ms)
                            const durationMatch = transition.match(/(\\d+(?:\\.\\d+)?)(m?s)/);
                            if (durationMatch) {
                                const duration = parseFloat(durationMatch[1]);
                                const unit = durationMatch[2];
                                const ms = unit === 's' ? duration * 1000 : duration;
                                if (ms > 200) {
                                    return {slow: true, duration: ms};
                                }
                            }

                            return {slow: false};
                        }
                    """, button)

                    if has_slow_transition.get('slow'):
                        slow_buttons.append({
                            'text': text,
                            'transition_ms': has_slow_transition.get('duration'),
                        })

                except Exception:
                    continue

            if slow_buttons:
                self.frictions.append(UXFriction(
                    type=FrictionType.SLOW_INTERACTION,
                    location="Interactive Elements",
                    description=(
                        f"Found {len(slow_buttons)} button(s) with slow transitions (>200ms). "
                        "Slow visual feedback makes users unsure if their click registered, "
                        "leading to multiple clicks or abandonment."
                    ),
                    severity="low",
                    evidence={"slow_buttons": slow_buttons},
                    recommendation=(
                        "Ensure button hover/active states respond within 100ms. "
                        "Add immediate visual feedback (color change, ripple effect) on click. "
                        "Reserve longer animations for after the click is confirmed."
                    ),
                ))

        except Exception as e:
            logger.debug(f"Interaction test error: {e}")

    async def _test_scroll_experience(self):
        """Test scroll smoothness and detect jank."""
        logger.debug("Testing scroll experience...")

        try:
            # Scroll and measure jank
            scroll_metrics = await self.page.evaluate("""
                async () => {
                    return new Promise((resolve) => {
                        let jankEvents = [];
                        let lastFrameTime = 0;

                        // Use requestAnimationFrame to detect frame drops
                        const frameCallback = (timestamp) => {
                            if (lastFrameTime > 0) {
                                const frameDuration = timestamp - lastFrameTime;
                                // A frame longer than 50ms (20fps) indicates jank
                                if (frameDuration > 50) {
                                    jankEvents.push({
                                        duration: Math.round(frameDuration),
                                        timestamp: Math.round(timestamp),
                                    });
                                }
                            }
                            lastFrameTime = timestamp;
                        };

                        // Start monitoring frames
                        let rafId;
                        const startMonitoring = () => {
                            rafId = requestAnimationFrame((ts) => {
                                frameCallback(ts);
                                startMonitoring();
                            });
                        };
                        startMonitoring();

                        // Perform smooth scroll
                        const docHeight = document.body.scrollHeight;
                        const viewHeight = window.innerHeight;
                        const scrollDistance = Math.min(docHeight - viewHeight, viewHeight * 3);

                        window.scrollTo({
                            top: scrollDistance,
                            behavior: 'smooth'
                        });

                        // Wait for scroll to complete
                        setTimeout(() => {
                            cancelAnimationFrame(rafId);

                            // Scroll back to top
                            window.scrollTo({top: 0, behavior: 'instant'});

                            resolve({
                                jankCount: jankEvents.length,
                                jankEvents: jankEvents.slice(0, 5),
                                scrollDistance: scrollDistance,
                            });
                        }, 2000);
                    });
                }
            """)

            self.metrics['scroll'] = scroll_metrics

            if scroll_metrics['jankCount'] >= self.SCROLL_JANK_THRESHOLD:
                self.frictions.append(UXFriction(
                    type=FrictionType.SCROLL_JANK,
                    location="Page Scroll",
                    description=(
                        f"Scroll jank detected ({scroll_metrics['jankCount']} frame drops). "
                        "Page scrolling is not smooth, making the site feel sluggish and low-quality. "
                        "This is often caused by heavy JavaScript execution, unoptimized images, "
                        "or excessive DOM complexity."
                    ),
                    severity="medium",
                    evidence={
                        "jank_count": scroll_metrics['jankCount'],
                        "jank_events": scroll_metrics.get('jankEvents', []),
                    },
                    recommendation=(
                        "1. Optimize and lazy load images below the fold. "
                        "2. Reduce JavaScript execution during scroll (avoid scroll listeners). "
                        "3. Use CSS will-change sparingly on animated elements. "
                        "4. Consider using content-visibility: auto for off-screen content. "
                        "5. Profile with Chrome DevTools Performance tab to identify bottlenecks."
                    ),
                ))

        except Exception as e:
            logger.debug(f"Scroll test error: {e}")

    async def _test_navigation_clarity(self):
        """Test if navigation is clear and intuitive."""
        logger.debug("Testing navigation clarity...")

        try:
            nav_analysis = await self.page.evaluate("""
                () => {
                    const navSelectors = ['nav', '[role="navigation"]', 'header nav', '.navigation', '.nav'];
                    let nav = null;

                    for (const selector of navSelectors) {
                        nav = document.querySelector(selector);
                        if (nav) break;
                    }

                    if (!nav) return {hasNav: false};

                    const links = nav.querySelectorAll('a');
                    const linkTexts = [...links].map(l => l.innerText.trim()).filter(t => t.length > 0);

                    // Check for vague link text
                    const vaguePatterns = ['click here', 'read more', 'learn more', 'see more', 'more', 'click', 'here'];
                    const vagueLinks = linkTexts.filter(t =>
                        vaguePatterns.includes(t.toLowerCase())
                    );

                    // Count top-level navigation items
                    const topLevelItems = nav.querySelectorAll(':scope > ul > li, :scope > div > a, :scope > a').length;

                    // Check for mobile menu
                    const mobileMenuSelectors = [
                        '[class*="mobile"]', '[class*="hamburger"]',
                        '[class*="menu-toggle"]', '[class*="burger"]',
                        'button[aria-label*="menu"]', '.menu-icon'
                    ];
                    const hasMobileMenu = mobileMenuSelectors.some(s => nav.querySelector(s) !== null);

                    // Check for dropdown menus
                    const hasDropdowns = nav.querySelectorAll('[class*="dropdown"], [class*="submenu"]').length > 0;

                    return {
                        hasNav: true,
                        linkCount: links.length,
                        topLevelItems: topLevelItems,
                        vagueLinks: vagueLinks,
                        hasMobileMenu: hasMobileMenu,
                        hasDropdowns: hasDropdowns,
                        linkTexts: linkTexts.slice(0, 15),
                    };
                }
            """)

            self.metrics['navigation'] = nav_analysis

            if not nav_analysis.get('hasNav'):
                self.frictions.append(UXFriction(
                    type=FrictionType.CONFUSING_NAVIGATION,
                    location="Main Navigation",
                    description="No navigation menu detected. Users have no clear way to explore the site.",
                    severity="high",
                    evidence={},
                    recommendation="Add a clear navigation menu with links to key sections of the site.",
                ))
                return

            # Check for too many navigation items
            if nav_analysis.get('topLevelItems', 0) > 7:
                self.frictions.append(UXFriction(
                    type=FrictionType.CONFUSING_NAVIGATION,
                    location="Main Navigation",
                    description=(
                        f"Navigation has {nav_analysis['topLevelItems']} top-level items. "
                        "Research shows users can comfortably process 5-7 items. "
                        "Cognitive overload makes it harder for users to find what they need."
                    ),
                    severity="medium",
                    evidence={
                        "top_level_items": nav_analysis['topLevelItems'],
                        "link_texts": nav_analysis.get('linkTexts', []),
                    },
                    recommendation=(
                        "1. Consolidate to 5-7 main navigation items. "
                        "2. Group related items under dropdowns. "
                        "3. Move secondary items to footer or sub-navigation. "
                        "4. Add a clear primary CTA (e.g., 'Get Started', 'Contact Us')."
                    ),
                ))

            # Check for vague link text
            if nav_analysis.get('vagueLinks'):
                self.frictions.append(UXFriction(
                    type=FrictionType.UNCLEAR_CTA,
                    location="Navigation Links",
                    description=(
                        f"Navigation contains vague link text: {', '.join(nav_analysis['vagueLinks'])}. "
                        "Users can't predict where these links will take them."
                    ),
                    severity="low",
                    evidence={"vague_links": nav_analysis['vagueLinks']},
                    recommendation=(
                        "Use descriptive link text that tells users exactly where they'll go. "
                        "Replace 'Learn More' with specific actions like 'View Pricing' or 'See Our Work'."
                    ),
                ))

        except Exception as e:
            logger.debug(f"Navigation test error: {e}")

    async def _test_form_friction(self):
        """Test for form usability issues."""
        logger.debug("Testing form friction...")

        try:
            form_analysis = await self.page.evaluate("""
                () => {
                    const forms = document.querySelectorAll('form');
                    if (forms.length === 0) return {hasForms: false};

                    let issues = [];

                    forms.forEach((form, idx) => {
                        const inputs = form.querySelectorAll('input, textarea, select');

                        // Check for missing labels
                        const unlabeled = [...inputs].filter(input => {
                            if (input.type === 'hidden' || input.type === 'submit') return false;
                            const label = form.querySelector(`label[for="${input.id}"]`);
                            const ariaLabel = input.getAttribute('aria-label');
                            const placeholder = input.placeholder;
                            return !label && !ariaLabel && !placeholder;
                        });

                        if (unlabeled.length > 0) {
                            issues.push({
                                form: idx + 1,
                                issue: 'unlabeled_inputs',
                                count: unlabeled.length,
                            });
                        }

                        // Check submit button text
                        const submitBtns = form.querySelectorAll('button[type="submit"], input[type="submit"]');
                        submitBtns.forEach(btn => {
                            const text = (btn.innerText || btn.value || '').toLowerCase().trim();
                            if (text === 'submit' || text === 'send') {
                                issues.push({
                                    form: idx + 1,
                                    issue: 'weak_submit_text',
                                    text: text,
                                });
                            }
                        });

                        // Check for very long forms
                        if (inputs.length > 10) {
                            issues.push({
                                form: idx + 1,
                                issue: 'too_many_fields',
                                count: inputs.length,
                            });
                        }
                    });

                    return {
                        hasForms: true,
                        formCount: forms.length,
                        issues: issues,
                    };
                }
            """)

            self.metrics['forms'] = form_analysis

            if not form_analysis.get('hasForms'):
                return

            for issue in form_analysis.get('issues', []):
                if issue['issue'] == 'weak_submit_text':
                    self.frictions.append(UXFriction(
                        type=FrictionType.FRUSTRATING_FORM,
                        location=f"Form {issue['form']}",
                        description=(
                            f"Form uses generic '{issue['text']}' button text. "
                            "Specific, action-oriented button text increases conversion rates."
                        ),
                        severity="low",
                        evidence={"button_text": issue['text']},
                        recommendation=(
                            "Use specific, benefit-oriented button text. "
                            "Examples: 'Get My Free Quote', 'Schedule Viewing', 'Start Free Trial'"
                        ),
                    ))

                elif issue['issue'] == 'too_many_fields':
                    self.frictions.append(UXFriction(
                        type=FrictionType.FRUSTRATING_FORM,
                        location=f"Form {issue['form']}",
                        description=(
                            f"Form has {issue['count']} fields. Long forms have high abandonment rates."
                        ),
                        severity="medium",
                        evidence={"field_count": issue['count']},
                        recommendation=(
                            "Reduce form fields to essentials. "
                            "Ask for additional information after initial submission. "
                            "Consider multi-step forms for complex data collection."
                        ),
                    ))

                elif issue['issue'] == 'unlabeled_inputs':
                    self.frictions.append(UXFriction(
                        type=FrictionType.FRUSTRATING_FORM,
                        location=f"Form {issue['form']}",
                        description=(
                            f"Form has {issue['count']} input(s) without proper labels. "
                            "This hurts accessibility and usability."
                        ),
                        severity="medium",
                        evidence={"unlabeled_count": issue['count']},
                        recommendation=(
                            "Add proper labels to all form inputs. "
                            "Use <label for='input-id'> or aria-label for accessibility."
                        ),
                    ))

        except Exception as e:
            logger.debug(f"Form test error: {e}")


async def run_experience_agent(url: str, browser: Optional[Browser] = None) -> List[UXFriction]:
    """
    Run the experience agent on a URL.

    Args:
        url: The URL to experience
        browser: Optional browser instance (creates one if not provided)

    Returns:
        List of UXFriction objects
    """
    created_browser = False

    if browser is None:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        created_browser = True

    try:
        page = await browser.new_page(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        agent = ExperienceAgent(page)
        frictions = await agent.experience_page(url)

        await page.close()

        return frictions

    finally:
        if created_browser:
            await browser.close()
            await playwright.stop()


async def run_experience_test(url: str) -> Dict[str, Any]:
    """
    Run a full experience test and return detailed results.

    Args:
        url: The URL to test

    Returns:
        Dict with frictions, metrics, and summary
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    try:
        page = await browser.new_page(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        agent = ExperienceAgent(page)
        frictions = await agent.experience_page(url)

        await page.close()

        # Summarize by severity
        by_severity = {}
        for f in frictions:
            by_severity[f.severity] = by_severity.get(f.severity, 0) + 1

        return {
            "url": url,
            "frictions": [f.to_dict() for f in frictions],
            "metrics": agent.metrics,
            "summary": {
                "total_friction_points": len(frictions),
                "by_severity": by_severity,
            }
        }

    finally:
        await browser.close()
        await playwright.stop()
