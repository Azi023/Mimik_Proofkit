"""Data models for the collector module."""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class CTAInfo(BaseModel):
    """Information about a Call-to-Action element."""
    text: str
    type: str  # "link" or "button"
    href: Optional[str] = None
    is_visible: bool = True
    is_above_fold: bool = False
    selector: Optional[str] = None


class FormInfo(BaseModel):
    """Information about a form element."""
    action: Optional[str] = None
    method: str = "GET"
    field_count: int = 0
    required_count: int = 0
    has_email_field: bool = False
    has_phone_field: bool = False
    submit_button_text: str = "Submit"


class NavigationInfo(BaseModel):
    """Information about page navigation structure."""
    links: List[Dict[str, str]] = []
    has_hamburger: bool = False
    depth: int = 1


class PageSnapshot(BaseModel):
    """Snapshot data for a single page."""
    url: str
    title: str = ""
    headings: Dict[str, List[str]] = {"h1": [], "h2": [], "h3": []}
    ctas: List[CTAInfo] = []
    mobile_ctas: List[CTAInfo] = []
    forms: List[FormInfo] = []
    navigation: Optional[NavigationInfo] = None
    whatsapp_links: List[Dict[str, Any]] = []
    contact_info: Dict[str, Any] = {}
    screenshots: List[str] = []
    hamburger_menu_works: Optional[bool] = None
    console_errors: List[str] = []
    html_content: Optional[str] = None
    meta_tags: Dict[str, str] = {}


class SnapshotData(BaseModel):
    """Complete snapshot data from Playwright collector."""
    url: str
    pages: List[PageSnapshot] = []
    screenshots: List[str] = []
    total_ctas: int = 0
    total_forms: int = 0


class CoreWebVitals(BaseModel):
    """Core Web Vitals metrics from Lighthouse."""
    lcp: Optional[float] = None  # Largest Contentful Paint (ms)
    fid: Optional[float] = None  # First Input Delay (ms)
    cls: Optional[float] = None  # Cumulative Layout Shift
    inp: Optional[float] = None  # Interaction to Next Paint (ms)
    ttfb: Optional[float] = None  # Time to First Byte (ms)
    tbt: Optional[float] = None  # Total Blocking Time (ms)
    fcp: Optional[float] = None  # First Contentful Paint (ms)
    si: Optional[float] = None   # Speed Index


class LighthouseScores(BaseModel):
    """Lighthouse category scores."""
    performance: Optional[float] = None
    accessibility: Optional[float] = None
    best_practices: Optional[float] = None
    seo: Optional[float] = None


class LighthouseOpportunity(BaseModel):
    """A Lighthouse optimization opportunity."""
    id: str
    title: str
    description: str = ""
    score: Optional[float] = None
    savings_ms: Optional[float] = None
    savings_bytes: Optional[int] = None
    display_value: str = ""


class LighthouseData(BaseModel):
    """Complete Lighthouse audit data."""
    url: str
    mobile: Dict[str, Any] = {}
    desktop: Dict[str, Any] = {}
    mobile_scores: LighthouseScores = LighthouseScores()
    desktop_scores: LighthouseScores = LighthouseScores()
    mobile_cwv: CoreWebVitals = CoreWebVitals()
    desktop_cwv: CoreWebVitals = CoreWebVitals()
    opportunities: List[LighthouseOpportunity] = []


class SecurityHeaders(BaseModel):
    """Security header analysis results."""
    present: Dict[str, str] = {}
    missing: List[str] = []
    has_hsts: bool = False
    has_csp: bool = False
    has_xframe: bool = False
    score: float = 0


class SSLInfo(BaseModel):
    """SSL certificate information."""
    valid: bool = False
    issuer: Optional[str] = None
    expires: Optional[str] = None
    subject: Optional[str] = None
    error: Optional[str] = None
    days_until_expiry: Optional[int] = None


class HttpProbeData(BaseModel):
    """HTTP probe results."""
    url: str
    final_url: str = ""
    status_code: int = 0
    redirect_chain: List[str] = []
    redirect_count: int = 0
    response_time_ms: float = 0
    headers: Dict[str, str] = {}
    security_headers: SecurityHeaders = SecurityHeaders()
    ssl_info: Optional[SSLInfo] = None
    server: Optional[str] = None
    robots_txt: Optional[str] = None
    sitemap_exists: bool = False
    sitemap_url: Optional[str] = None


class StackInfo(BaseModel):
    """Detected technology stack information."""
    cms: Optional[str] = None  # WordPress, Shopify, etc.
    framework: Optional[str] = None  # React, Vue, Angular, etc.
    server: Optional[str] = None  # nginx, Apache, etc.
    analytics: List[str] = []  # Google Analytics, etc.
    tag_managers: List[str] = []  # GTM, etc.
    cdn: Optional[str] = None  # Cloudflare, etc.
    ecommerce_platform: Optional[str] = None  # WooCommerce, Magento, etc.
    other: List[str] = []  # Other detected technologies


class BusinessSignals(BaseModel):
    """Signals for business type detection."""
    detected_type: Optional[str] = None
    confidence: float = 0.0
    keyword_matches: Dict[str, List[str]] = {}
    feature_indicators: List[str] = []
    industry_signals: List[str] = []


class RawData(BaseModel):
    """Complete raw data from all collectors."""
    url: str
    mode: str  # "fast" or "full"
    pages_audited: List[str] = []
    snapshot: SnapshotData = SnapshotData(url="")
    lighthouse: LighthouseData = LighthouseData(url="")
    http_probe: HttpProbeData = HttpProbeData(url="", final_url="")
    detected_stack: StackInfo = StackInfo()
    business_signals: BusinessSignals = BusinessSignals()
    collected_at: Optional[str] = None
    collection_errors: List[str] = []
