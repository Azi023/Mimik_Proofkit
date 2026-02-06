# Mimik ProofKit - Phase 5 Implementation Plan

## Current Status Summary

**Working:**
- ✅ 274 tests passing
- ✅ OpenAI integration working
- ✅ Pencil export module created
- ✅ Visual QA rules implemented
- ✅ API server running (localhost:8000)
- ✅ Frontend running (localhost:3001)
- ✅ API key generated: `pk_dev_O1ciZo0BT0HBZWzQrbpalfvo6cDFSZE0`
- ✅ API connected in Settings page (showing "Connected - v0.1.0")

**Issues to Fix:**
- ❌ Frontend getting 401 Unauthorized when creating audits
- ❌ Pencil integration not tested end-to-end
- ❌ Report template (Seven Tides style) not integrated

**New Features to Add:**
- 🆕 Intelligent QA Feature Discovery
- 🆕 Multi-Agent Audit System
- 🆕 Automated Script Generation
- 🆕 Clerk Authentication (optional)

---

## Part 1: Fix API Authentication Issue

### Problem Analysis

Looking at your screenshot, the frontend shows:
- Settings page: "Connected - v0.1.0" ✅
- New Audit page: "401 Unauthorized" ❌

This suggests the API key is stored in localStorage but not being sent correctly in requests.

### 1.1 Debug the Issue

```bash
# Check if API key is being sent correctly
# In browser console (F12 → Console), run:
localStorage.getItem('proofkit_api_key')

# Should show: pk_dev_O1ciZo0BT0HBZWzQrbpalfvo6cDFSZE0
```

### 1.2 Fix Frontend API Client

The issue is likely in how the API key is sent. Update `frontend/src/lib/api.ts`:

```typescript
// frontend/src/lib/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to get API key from localStorage
function getApiKey(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('proofkit_api_key');
}

// Base fetch wrapper with auth
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const apiKey = getApiKey();
  
  if (!apiKey) {
    throw new Error('No API key configured. Please add your API key in Settings.');
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    // Try both formats - header and Bearer token
    'Authorization': `Bearer ${apiKey}`,
    'X-API-Key': apiKey,
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    // Important: include credentials for CORS
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// API Functions
export async function createAudit(data: CreateAuditRequest): Promise<AuditResponse> {
  return fetchApi<AuditResponse>('/v1/audits', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getAudit(id: string): Promise<AuditResponse> {
  return fetchApi<AuditResponse>(`/v1/audits/${id}`);
}

export async function listAudits(params?: ListAuditsParams): Promise<AuditListResponse> {
  const query = params ? '?' + new URLSearchParams(params as any).toString() : '';
  return fetchApi<AuditListResponse>(`/v1/audits${query}`);
}

export async function testConnection(): Promise<{ status: string; version: string }> {
  const apiKey = getApiKey();
  if (!apiKey) {
    throw new Error('No API key');
  }
  
  const response = await fetch(`${API_BASE}/v1/health`, {
    headers: {
      'Authorization': `Bearer ${apiKey}`,
    },
  });
  
  if (!response.ok) {
    throw new Error('Connection failed');
  }
  
  return response.json();
}

// Types
export interface CreateAuditRequest {
  url: string;
  mode: 'fast' | 'full';
  business_type?: string;
  conversion_goal?: string;
  generate_concept?: boolean;
}

export interface AuditResponse {
  audit_id: string;
  status: 'queued' | 'processing' | 'complete' | 'failed';
  url?: string;
  created_at: string;
  completed_at?: string;
  scorecard?: Record<string, number>;
  finding_count?: number;
}

export interface ListAuditsParams {
  limit?: number;
  offset?: number;
  status?: string;
}

export interface AuditListResponse {
  audits: AuditResponse[];
  total: number;
  limit: number;
  offset: number;
}
```

### 1.3 Fix Backend CORS and Auth

Update `proofkit/api/main.py`:

```python
# proofkit/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI(
        title="Mimik ProofKit API",
        description="Website Audit QA Engine",
        version="0.1.0",
    )
    
    # CORS - Allow frontend origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # ... rest of app setup
    return app
```

### 1.4 Fix Auth Middleware

Update `proofkit/api/auth/api_keys.py` to accept both header formats:

```python
# proofkit/api/auth/api_keys.py

from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional

# Accept API key in multiple ways
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
api_key_header_alt = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def get_api_key(
    request: Request,
    auth_header: Optional[str] = Security(api_key_header),
    x_api_key: Optional[str] = Security(api_key_header_alt),
    query_key: Optional[str] = Security(api_key_query),
) -> str:
    """Extract API key from various sources."""
    
    # Try Authorization header (Bearer token)
    if auth_header:
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return auth_header
    
    # Try X-API-Key header
    if x_api_key:
        return x_api_key
    
    # Try query parameter
    if query_key:
        return query_key
    
    raise HTTPException(
        status_code=401,
        detail="Missing API key. Provide via Authorization header (Bearer token), X-API-Key header, or api_key query parameter.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def verify_api_key(api_key: str = Security(get_api_key)) -> dict:
    """Verify API key and return user."""
    from ..database.crud import get_user_by_api_key
    
    user = await get_user_by_api_key(api_key)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
```

---

## Part 2: Pencil.dev Integration with Seven Tides Template

### 2.1 Extract Template Structure from Figma

Based on your Seven Tides Figma template (13 pages), here's the structure:

```
Page 00: Cover Page
  - "hello." logo
  - "Website Performance & Inspection Report"
  - Client name
  - "Mimik Creations" footer
  - Gradient accent

Page 01: Executive Summary
  - Purpose of this audit (left column)
  - Audit Framework (4 bullet points)
  - Audit Status

Page 02: Audit Scope & Methodology
  - Audit Scope (4 areas)
  - Methodology (5 methods)

Page 03: Web Design & UX Audit
  - Objective
  - Evaluation table (5 areas)
  - Findings/Comments column

Page 04: UX Findings Detail
  - Custom Cursor Behavior
  - Above-the-fold Rendering
  - Portfolio Navigation Confusion
  - UX Recommendations

Page 05: Technical SEO Audit
  - Performance drivers
  - On-page SEO
  - Content gaps

Page 06: SEO Findings Detail
  - Technical SEO Recommendations
  - Content Recommendations

Page 07: Lead Generation Audit
  - CTA Strategy
  - Lead Capture
  - User Journey
  - Trust & Reassurance

Page 08: Conversion Findings Detail
  - Lead Path Clarity
  - Form Friction
  - Missing Trust Signals
  - Conversion Recommendations

Page 09: Maintenance Audit
  - Infrastructure
  - Security
  - Code Health
  - Maintenance Readiness

Page 10: Maintenance Findings Detail
  - Infrastructure Assessment
  - Security Assessment
  - Code Health Assessment

Page 11: Closing Note
  - Summary
  - Benefits list
  - Next steps
```

### 2.2 Create Template Configuration

Create `proofkit/report_builder/templates/seven_tides.py`:

```python
"""
Seven Tides Report Template Configuration

Defines the exact structure and prompts for generating reports
that match the Seven Tides Figma template style.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class PageTemplate:
    """Template for a single report page."""
    page_number: str
    title: str
    layout: str  # "cover", "two-column", "table", "findings", "closing"
    sections: List[Dict[str, Any]] = field(default_factory=list)
    pencil_prompt: str = ""


SEVEN_TIDES_TEMPLATE = {
    "name": "Seven Tides Professional",
    "description": "Luxury real estate audit report style",
    "brand": {
        "logo_text": "hello.",
        "company": "Mimik Creations",
        "primary_color": "#1a1a1a",
        "accent_color": "#4098F9",
        "gradient": "pink → purple → blue",
    },
    "pages": [
        PageTemplate(
            page_number="00",
            title="Cover",
            layout="cover",
            pencil_prompt="""
Design a professional report cover page:

LAYOUT:
- Top left: "hello." in large bold black text (48px)
- Page number "00" in top right corner
- Center-left: Main title "Website Performance & Inspection Report" (32px bold)
- Below title: Client name "{client_name}" in lighter gray
- Bottom left: "Mimik Creations" with underline
- Bottom right: Gradient blob (pink → purple → blue, organic shape)

STYLE:
- Background: White (#FFFFFF)
- Text: Dark gray (#1a1a1a)
- Clean, minimal, professional
- Generous whitespace
- Font: Inter or similar sans-serif
"""
        ),
        
        PageTemplate(
            page_number="01",
            title="Executive Summary",
            layout="two-column",
            sections=[
                {"name": "PURPOSE OF THIS AUDIT", "type": "paragraph"},
                {"name": "AUDIT FRAMEWORK", "type": "bullet_list"},
                {"name": "AUDIT STATUS", "type": "paragraph"},
            ],
            pencil_prompt="""
Design an executive summary page:

LAYOUT:
- Page number "01" in top right
- Title "Executive Summary" with decorative line above

LEFT COLUMN (60%):
- "PURPOSE OF THIS AUDIT" section heading (small caps, gray)
- Paragraph: {executive_summary}

- "AUDIT FRAMEWORK" section heading
- Bullet list:
  • Web Design & User Experience (UX)
  • Technical SEO & Content Effectiveness
  • Lead Generation
  • General Maintenance & Site Health

RIGHT COLUMN (40%):
- "AUDIT STATUS" section heading
- Status paragraph

STYLE:
- Two-column layout
- Section headings in small caps, gray (#666)
- Body text in dark (#1a1a1a)
- Clean lines separating sections
"""
        ),
        
        PageTemplate(
            page_number="02",
            title="Audit Scope & Methodology",
            layout="two-column",
            sections=[
                {"name": "AUDIT SCOPE", "type": "numbered_list"},
                {"name": "METHODOLOGY", "type": "bullet_list"},
            ],
            pencil_prompt="""
Design an audit scope page:

LAYOUT:
- Page number "02" in top right
- Title "Audit Scope & Methodology" with decorative line

LEFT COLUMN:
- "AUDIT SCOPE" heading
- Numbered list:
  1. Web Design & UX Audit
  2. Technical SEO & Content Audit
  3. Lead Generation & Conversion Audit
  4. General Maintenance & Site Health Audit

- "Each section includes:" subheading
- Bullet list: Evaluation criteria, Observations, Impact assessment, Recommendations

RIGHT COLUMN:
- "METHODOLOGY" heading
- Bullet list of methods used
"""
        ),
        
        PageTemplate(
            page_number="03",
            title="Web Design & User Experience (UX) Audit",
            layout="table",
            sections=[
                {"name": "OBJECTIVE", "type": "paragraph"},
                {"name": "EVALUATION TABLE", "type": "table", "columns": ["Evaluation Areas", "Details", "Findings / Comments"]},
            ],
            pencil_prompt="""
Design a UX audit findings page:

LAYOUT:
- Page number "03" in top right
- Title "Web Design & User Experience (UX) Audit"

OBJECTIVE SECTION:
- Small text explaining the audit purpose

TABLE:
- 3 columns: "Evaluation Areas", "Details", "Findings / Comments"
- Rows for each UX area:
  {ux_findings_table}

STYLE:
- Clean table with subtle borders
- Alternating row backgrounds (white / #F5F5F5)
- Findings column may have color-coded status indicators
"""
        ),
        
        # ... Continue for all 13 pages
    ],
}


def get_page_prompt(page_number: str, data: Dict[str, Any]) -> str:
    """Get the Pencil prompt for a specific page with data filled in."""
    for page in SEVEN_TIDES_TEMPLATE["pages"]:
        if page.page_number == page_number:
            return page.pencil_prompt.format(**data)
    return ""


def get_full_report_prompt(data: Dict[str, Any]) -> str:
    """Generate complete multi-page report prompt."""
    prompt = f"""
Create a professional {len(SEVEN_TIDES_TEMPLATE['pages'])}-page website audit report.

BRAND GUIDELINES:
- Logo: "{SEVEN_TIDES_TEMPLATE['brand']['logo_text']}"
- Company: {SEVEN_TIDES_TEMPLATE['brand']['company']}
- Colors: Primary {SEVEN_TIDES_TEMPLATE['brand']['primary_color']}, Accent {SEVEN_TIDES_TEMPLATE['brand']['accent_color']}
- Style: Clean, minimal, professional, generous whitespace

CLIENT: {data.get('client_name', 'Unknown')}
URL: {data.get('url', '')}

"""
    
    for page in SEVEN_TIDES_TEMPLATE["pages"]:
        prompt += f"\n\n--- PAGE {page.page_number}: {page.title} ---\n"
        prompt += page.pencil_prompt.format(**data)
    
    return prompt
```

### 2.3 Update Pencil Export with Template

Update `proofkit/report_builder/pencil_export.py` to use templates:

```python
# Add to pencil_export.py

from .templates.seven_tides import SEVEN_TIDES_TEMPLATE, get_full_report_prompt

class PencilReportGenerator:
    """Generate Pencil-compatible prompts using templates."""
    
    def __init__(self, report: Report, template: str = "seven_tides"):
        self.report = report
        self.template_name = template
        self.findings_by_category = self._group_findings()
        
        # Load template
        if template == "seven_tides":
            self.template = SEVEN_TIDES_TEMPLATE
        else:
            self.template = SEVEN_TIDES_TEMPLATE  # Default
    
    def _prepare_template_data(self) -> dict:
        """Prepare data for template substitution."""
        return {
            "client_name": self._extract_client_name(),
            "url": self.report.meta.url,
            "executive_summary": self.report.narrative.executive_summary if self.report.narrative else "",
            "ux_findings_table": self._format_findings_table("UX"),
            "seo_findings_table": self._format_findings_table("SEO"),
            "conversion_findings_table": self._format_findings_table("CONVERSION"),
            "security_findings_table": self._format_findings_table("SECURITY"),
            "quick_wins": self._format_list(self.report.narrative.key_wins if self.report.narrative else []),
            "priorities": self._format_list(self.report.narrative.priority_roadmap if self.report.narrative else []),
            "scorecard": self._format_scorecard_visual(),
        }
    
    def generate_full_report_prompt(self) -> str:
        """Generate complete report prompt using template."""
        data = self._prepare_template_data()
        return get_full_report_prompt(data)
    
    def _format_findings_table(self, category: str) -> str:
        """Format findings as table rows."""
        findings = self.findings_by_category.get(category, [])
        rows = []
        for f in findings[:5]:
            rows.append(f"| {f.title} | {f.summary[:100]} | {f.recommendation[:100]} |")
        return "\n".join(rows)
    
    def _format_scorecard_visual(self) -> str:
        """Format scorecard for visual display."""
        if not self.report.scorecard:
            return "Scores pending"
        
        lines = []
        for cat, score in self.report.scorecard.items():
            bar = "█" * (score // 10) + "░" * (10 - score // 10)
            color = "green" if score >= 75 else "yellow" if score >= 50 else "red"
            lines.append(f"{cat}: [{bar}] {score}/100")
        return "\n".join(lines)
```

### 2.4 CLI Command for Pencil with Template

```bash
# Usage
proofkit export-pencil --run-dir ./runs/run_XXX --template seven_tides

# This generates:
# - pencil/pencil_full_report.txt (complete 13-page prompt)
# - pencil/page_00_cover.txt
# - pencil/page_01_executive_summary.txt
# ... etc
```

---

## Part 3: Intelligent QA Feature Discovery

This is the most exciting new feature - making ProofKit discover and test features automatically.

### 3.1 Create Intelligent QA Agent

Create `agents/AGENT_INTELLIGENT_QA.md`:

```markdown
# Intelligent QA Agent

## Identity

You are the **Intelligent QA Agent** for Mimik ProofKit. You automatically discover interactive features on web pages and generate test cases for them.

## Capabilities

1. **Feature Discovery** - Scan pages to find all interactive elements
2. **Behavior Inference** - Understand what each element should do
3. **Test Generation** - Create test scripts for each feature
4. **Test Execution** - Run tests and report results
5. **Regression Detection** - Compare against baselines

## Files You Own

```
proofkit/intelligent_qa/
├── __init__.py
├── feature_discovery.py     # Discover interactive elements
├── behavior_inference.py    # Infer expected behaviors
├── test_generator.py        # Generate test scripts
├── test_runner.py           # Execute tests
├── baseline_manager.py      # Manage test baselines
└── report_generator.py      # Generate QA reports
```
```

### 3.2 Feature Discovery Module

Create `proofkit/intelligent_qa/feature_discovery.py`:

```python
"""
Intelligent Feature Discovery

Automatically discovers all interactive elements on a web page
and categorizes them by type and expected behavior.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from playwright.async_api import Page, Locator


class FeatureType(str, Enum):
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
    
    def __init__(self, page: Page):
        self.page = page
        self.features: List[DiscoveredFeature] = []
        self.feature_count = 0
    
    async def discover_all(self) -> List[DiscoveredFeature]:
        """Discover all interactive features on the page."""
        
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
            except Exception:
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
                    # Skip if already discovered
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
        except:
            text = ""
        
        try:
            location = await self._get_element_location(element)
        except:
            location = "unknown"
        
        try:
            tag = await element.evaluate("el => el.tagName.toLowerCase()")
            class_name = await element.get_attribute("class") or ""
            element_id = await element.get_attribute("id") or ""
        except:
            tag = "unknown"
            class_name = ""
            element_id = ""
        
        feature = DiscoveredFeature(
            id=f"feat_{self.feature_count:04d}",
            type=feature_type,
            element=f"{tag}#{element_id}.{class_name.split()[0] if class_name else ''}",
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
        # Simple check - could be improved
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
        
        else:
            test_cases = [
                {"name": "Element visible", "action": "verify", "expected": "Element is visible"},
                {"name": "Interaction works", "action": "interact", "expected": "Expected behavior occurs"},
            ]
        
        return test_cases
```

### 3.3 Test Generator Module

Create `proofkit/intelligent_qa/test_generator.py`:

```python
"""
Intelligent Test Generator

Generates Playwright test scripts for discovered features.
"""

from typing import List
from pathlib import Path

from .feature_discovery import DiscoveredFeature, FeatureType


class TestGenerator:
    """Generates executable test scripts for discovered features."""
    
    def __init__(self, features: List[DiscoveredFeature], url: str):
        self.features = features
        self.url = url
    
    def generate_playwright_tests(self) -> str:
        """Generate a complete Playwright test file."""
        
        test_code = f'''"""
Auto-generated QA tests for {self.url}
Generated by Mimik ProofKit Intelligent QA
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="module")
def page(browser):
    """Create page and navigate to URL."""
    page = browser.new_page()
    page.goto("{self.url}")
    page.wait_for_load_state("networkidle")
    yield page
    page.close()


'''
        
        # Group features by type
        by_type = {}
        for f in self.features:
            if f.type not in by_type:
                by_type[f.type] = []
            by_type[f.type].append(f)
        
        # Generate test class for each type
        for feature_type, features in by_type.items():
            test_code += self._generate_test_class(feature_type, features)
        
        return test_code
    
    def _generate_test_class(
        self, 
        feature_type: FeatureType, 
        features: List[DiscoveredFeature]
    ) -> str:
        """Generate test class for a feature type."""
        
        class_name = f"Test{feature_type.value.replace('_', ' ').title().replace(' ', '')}"
        
        code = f'''
class {class_name}:
    """Tests for {feature_type.value} features."""
    
'''
        
        for feature in features[:5]:  # Limit to 5 per type
            code += self._generate_feature_tests(feature)
        
        return code
    
    def _generate_feature_tests(self, feature: DiscoveredFeature) -> str:
        """Generate tests for a single feature."""
        
        func_name = f"test_{feature.id}_{feature.type.value}"
        
        code = f'''
    def {func_name}(self, page: Page):
        """
        Feature: {feature.text[:50] or feature.type.value}
        Location: {feature.location}
        Expected: {feature.expected_behavior}
        """
'''
        
        # Generate test based on feature type
        if feature.type == FeatureType.WHATSAPP:
            code += '''
        # Find WhatsApp button
        whatsapp = page.locator("a[href*='wa.me'], a[href*='whatsapp']").first
        
        # Verify it exists and is visible
        expect(whatsapp).to_be_visible()
        
        # Check href format
        href = whatsapp.get_attribute("href")
        assert "wa.me" in href or "whatsapp" in href
        
        # Should open in new tab
        target = whatsapp.get_attribute("target")
        assert target == "_blank" or target is None  # Opens in same or new
'''
        
        elif feature.type == FeatureType.FORM:
            code += '''
        # Find form
        form = page.locator("form").first
        expect(form).to_be_visible()
        
        # Find required fields
        required = form.locator("[required]")
        
        # Try submit empty (should fail validation)
        submit_btn = form.locator("button[type='submit'], input[type='submit']").first
        submit_btn.click()
        
        # Check for validation message
        # Note: HTML5 validation or custom validation
        invalid = form.locator(":invalid")
        assert invalid.count() > 0 or page.locator(".error, .invalid").count() > 0
'''
        
        elif feature.type == FeatureType.NAVIGATION:
            code += '''
        # Find navigation
        nav = page.locator("nav, [role='navigation']").first
        expect(nav).to_be_visible()
        
        # Get all links
        links = nav.locator("a")
        link_count = links.count()
        assert link_count > 0, "Navigation should have links"
        
        # Check all links have href
        for i in range(min(link_count, 10)):
            link = links.nth(i)
            href = link.get_attribute("href")
            assert href is not None, f"Link {i} missing href"
'''
        
        elif feature.type == FeatureType.ACCORDION:
            code += '''
        # Find accordion
        accordion = page.locator(".accordion, [data-accordion], .faq").first
        
        if accordion.count() > 0:
            # Find toggle buttons
            toggles = accordion.locator("button, [role='button'], .accordion-header")
            
            if toggles.count() > 0:
                # Click first toggle
                first_toggle = toggles.first
                first_toggle.click()
                
                # Content should be visible after click
                page.wait_for_timeout(500)  # Animation
'''
        
        else:
            # Generic test
            code += f'''
        # Generic test for {feature.type.value}
        # Selector: {feature.element}
        element = page.locator("{feature.attributes.get('tag', '*')}").first
        
        if element.count() > 0:
            expect(element).to_be_visible()
'''
        
        return code
    
    def save_tests(self, output_dir: Path) -> Path:
        """Save generated tests to file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = output_dir / "test_generated_qa.py"
        test_code = self.generate_playwright_tests()
        test_file.write_text(test_code)
        
        return test_file
```

### 3.4 CLI Command for Intelligent QA

Add to CLI:

```python
@app.command()
def discover_features(
    url: str = typer.Argument(..., help="URL to analyze"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o"),
    generate_tests: bool = typer.Option(True, "--tests/--no-tests"),
):
    """
    Discover interactive features on a webpage and generate tests.
    
    Example:
        proofkit discover-features https://example.com --output ./qa_tests
    """
    import asyncio
    from proofkit.intelligent_qa.feature_discovery import FeatureDiscovery
    from proofkit.intelligent_qa.test_generator import TestGenerator
    
    async def run():
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            
            # Discover features
            discovery = FeatureDiscovery(page)
            features = await discovery.discover_all()
            
            await browser.close()
            return features
    
    console.print(f"[cyan]Discovering features on {url}...[/cyan]")
    features = asyncio.run(run())
    
    console.print(f"[green]✓ Found {len(features)} interactive features[/green]")
    
    # Display summary
    by_type = {}
    for f in features:
        by_type[f.type.value] = by_type.get(f.type.value, 0) + 1
    
    for ftype, count in sorted(by_type.items()):
        console.print(f"  {ftype}: {count}")
    
    # Generate tests
    if generate_tests:
        generator = TestGenerator(features, url)
        output = output_dir or Path("./qa_tests")
        test_file = generator.save_tests(output)
        console.print(f"\n[green]✓ Tests saved to {test_file}[/green]")
        console.print(f"Run with: pytest {test_file} -v")
```

---

## Part 4: Multi-Agent Audit System

### 4.1 Agent Orchestrator

Create `proofkit/agents/orchestrator.py`:

```python
"""
Multi-Agent Audit Orchestrator

Coordinates multiple specialized agents to perform comprehensive audits.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import asyncio

from proofkit.narrator.ai_client import get_ai_client


class AgentRole(str, Enum):
    DISCOVERY = "discovery"      # Discovers pages and features
    PERFORMANCE = "performance"  # Analyzes performance
    SECURITY = "security"        # Security analysis
    ACCESSIBILITY = "accessibility"
    SEO = "seo"
    UX = "ux"
    CONTENT = "content"
    COORDINATOR = "coordinator"  # Synthesizes results


@dataclass
class AgentTask:
    """Task for an agent to perform."""
    role: AgentRole
    objective: str
    context: Dict[str, Any]
    priority: int = 1


@dataclass 
class AgentResult:
    """Result from an agent."""
    role: AgentRole
    findings: List[Dict[str, Any]]
    suggestions: List[str]
    next_tasks: List[AgentTask]


class AuditAgent:
    """Individual AI agent with specialized role."""
    
    ROLE_PROMPTS = {
        AgentRole.DISCOVERY: """
You are a Discovery Agent. Your job is to:
1. Identify all pages on the website that need auditing
2. Discover interactive features on each page
3. Map the user journey flows
4. Identify critical conversion paths

Analyze the provided data and report what you find.
""",
        AgentRole.PERFORMANCE: """
You are a Performance Agent. Your job is to:
1. Analyze page load times and Core Web Vitals
2. Identify render-blocking resources
3. Check image optimization
4. Evaluate caching strategies
5. Measure Time to Interactive

Provide specific, actionable findings.
""",
        AgentRole.SECURITY: """
You are a Security Agent. Your job is to:
1. Check security headers (HSTS, CSP, X-Frame-Options)
2. Verify SSL/TLS configuration
3. Look for exposed sensitive data
4. Check for common vulnerabilities
5. Evaluate authentication mechanisms

Report security issues with severity levels.
""",
        AgentRole.UX: """
You are a UX Agent. Your job is to:
1. Evaluate navigation clarity
2. Check CTA visibility and effectiveness
3. Assess mobile responsiveness
4. Identify friction points
5. Evaluate visual hierarchy

Focus on conversion-impacting issues.
""",
        AgentRole.SEO: """
You are an SEO Agent. Your job is to:
1. Check meta tags and titles
2. Evaluate heading structure
3. Assess content quality signals
4. Check for indexing issues
5. Evaluate internal linking

Provide SEO improvement recommendations.
""",
        AgentRole.COORDINATOR: """
You are the Coordinator Agent. Your job is to:
1. Synthesize findings from all other agents
2. Prioritize issues by business impact
3. Identify patterns across findings
4. Create the executive summary
5. Determine what additional analysis is needed

Create a coherent narrative from all inputs.
""",
    }
    
    def __init__(self, role: AgentRole):
        self.role = role
        self.ai_client = get_ai_client()
        self.system_prompt = self.ROLE_PROMPTS.get(role, "You are a helpful audit agent.")
    
    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute a task and return results."""
        
        user_prompt = f"""
TASK: {task.objective}

CONTEXT:
{self._format_context(task.context)}

Analyze this and provide:
1. KEY FINDINGS (list specific issues found)
2. RECOMMENDATIONS (actionable suggestions)
3. ADDITIONAL ANALYSIS NEEDED (what else should be checked)

Format your response as structured JSON.
"""
        
        response = self.ai_client.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000,
        )
        
        return self._parse_response(response)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for the prompt."""
        import json
        return json.dumps(context, indent=2, default=str)
    
    def _parse_response(self, response: str) -> AgentResult:
        """Parse AI response into AgentResult."""
        import json
        
        try:
            # Try to parse as JSON
            data = json.loads(response)
            return AgentResult(
                role=self.role,
                findings=data.get("findings", []),
                suggestions=data.get("recommendations", []),
                next_tasks=[],
            )
        except json.JSONDecodeError:
            # Fall back to text parsing
            return AgentResult(
                role=self.role,
                findings=[{"text": response}],
                suggestions=[],
                next_tasks=[],
            )


class AgentOrchestrator:
    """Coordinates multiple agents for comprehensive audit."""
    
    def __init__(self):
        self.agents = {
            role: AuditAgent(role)
            for role in AgentRole
        }
        self.results: Dict[AgentRole, AgentResult] = {}
    
    async def run_audit(self, url: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run full multi-agent audit."""
        
        # Phase 1: Discovery
        discovery_result = await self.agents[AgentRole.DISCOVERY].execute(
            AgentTask(
                role=AgentRole.DISCOVERY,
                objective=f"Discover all features and pages on {url}",
                context={"url": url, "snapshot": raw_data.get("snapshot", {})},
            )
        )
        self.results[AgentRole.DISCOVERY] = discovery_result
        
        # Phase 2: Parallel specialized analysis
        analysis_tasks = [
            self._run_agent(AgentRole.PERFORMANCE, url, raw_data),
            self._run_agent(AgentRole.SECURITY, url, raw_data),
            self._run_agent(AgentRole.UX, url, raw_data),
            self._run_agent(AgentRole.SEO, url, raw_data),
        ]
        
        await asyncio.gather(*analysis_tasks)
        
        # Phase 3: Coordination and synthesis
        coordinator_result = await self.agents[AgentRole.COORDINATOR].execute(
            AgentTask(
                role=AgentRole.COORDINATOR,
                objective="Synthesize all findings into coherent report",
                context={
                    "url": url,
                    "agent_results": {
                        role.value: result.__dict__
                        for role, result in self.results.items()
                    },
                },
            )
        )
        self.results[AgentRole.COORDINATOR] = coordinator_result
        
        return self._compile_final_report()
    
    async def _run_agent(self, role: AgentRole, url: str, raw_data: Dict[str, Any]):
        """Run a single agent."""
        result = await self.agents[role].execute(
            AgentTask(
                role=role,
                objective=f"Analyze {role.value} aspects of {url}",
                context=raw_data,
            )
        )
        self.results[role] = result
    
    def _compile_final_report(self) -> Dict[str, Any]:
        """Compile all results into final report."""
        return {
            "agents_used": list(self.results.keys()),
            "findings_by_agent": {
                role.value: result.findings
                for role, result in self.results.items()
            },
            "all_suggestions": [
                suggestion
                for result in self.results.values()
                for suggestion in result.suggestions
            ],
            "executive_summary": self.results.get(
                AgentRole.COORDINATOR, 
                AgentResult(AgentRole.COORDINATOR, [], [], [])
            ).findings,
        }
```

---

## Part 5: Implementation Commands for Claude Code

Copy and paste these commands sequentially into Claude Code:

### Command 1: Fix API Authentication

```
Read the PHASE5_IMPLEMENTATION_PLAN.md file (Part 1) and implement the following:

1. Update frontend/src/lib/api.ts to properly send the API key in requests
2. Update proofkit/api/main.py to fix CORS for localhost:3001
3. Update proofkit/api/auth/api_keys.py to accept API key from multiple sources

Test by running both servers and trying to create an audit from the frontend.
```

### Command 2: Implement Pencil Template System

```
Read PHASE5_IMPLEMENTATION_PLAN.md Part 2 and implement:

1. Create proofkit/report_builder/templates/ directory
2. Create seven_tides.py template configuration matching the Figma design
3. Update pencil_export.py to use the template system
4. Update the CLI export-pencil command to accept --template option

Test with: proofkit export-pencil --run-dir ./runs/LATEST --template seven_tides
```

### Command 3: Implement Intelligent QA Discovery

```
Read PHASE5_IMPLEMENTATION_PLAN.md Part 3 and implement:

1. Create proofkit/intelligent_qa/ module
2. Implement feature_discovery.py for automatic feature detection
3. Implement test_generator.py for Playwright test generation
4. Add CLI command: proofkit discover-features

Test with: proofkit discover-features https://example.com
```

### Command 4: Implement Multi-Agent System

```
Read PHASE5_IMPLEMENTATION_PLAN.md Part 4 and implement:

1. Create proofkit/agents/orchestrator.py
2. Implement AuditAgent class with role-specific prompts
3. Implement AgentOrchestrator for parallel agent execution
4. Integrate with existing audit pipeline

Test the multi-agent system with a sample URL.
```

### Command 5: Update GitHub README

```
Update the README.md file to include:

1. Project overview and features
2. Installation instructions
3. Quick start guide
4. CLI command reference
5. API documentation link
6. Screenshots of the dashboard
7. Contributing guidelines

Make it professional and comprehensive.
```

---

## Summary

| Part | Feature | Priority | Effort |
|------|---------|----------|--------|
| 1 | Fix API Auth | HIGH | 1 hour |
| 2 | Pencil Templates | MEDIUM | 2 hours |
| 3 | Intelligent QA | HIGH | 4 hours |
| 4 | Multi-Agent | MEDIUM | 4 hours |
| 5 | README Update | LOW | 30 min |

Total estimated time: ~12 hours

The 401 error is likely just a header format issue - should be quick to fix. Once that's working, you can run real audits and test the full pipeline!
