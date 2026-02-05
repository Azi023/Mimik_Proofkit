# Mimik ProofKit - Foundation Document

## Project Overview

**Project Name:** Mimik ProofKit  
**Purpose:** Automated Website Audit QA Engineer for lead conversion  
**Owner:** Atheeque @ Mimik Creations  
**Status:** Foundation Planning Phase  
**Last Updated:** January 2026

---

## 1. Executive Summary

### What We're Building

A pipeline-based website audit system that:
1. Takes a URL → runs automated checks → extracts evidence
2. Summarizes + prioritizes findings using minimal AI tokens
3. Generates structured "report JSON" → exports to Figma-ready content
4. Optionally generates "Lovable concept prompts" for redesign demonstrations

### Business Value

- **Primary Use:** Convert leads by demonstrating website weaknesses professionally
- **Secondary Use:** Support existing client relationships (e.g., Seven Tides) with ongoing audits
- **Future Potential:** SaaS product / white-label for agencies

### Budget Constraint

**$10-$15/month API tokens** — This shapes the entire architecture:
- AI is used ONLY for interpretation, business impact writing, and recommendations
- All measurements use deterministic free tools (Lighthouse, Playwright, curl)

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MIMIK PROOFKIT                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  COLLECTOR  │───▶│  ANALYZER   │───▶│  NARRATOR   │             │
│  │   (Free)    │    │   (Free)    │    │   (AI $)    │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│        │                  │                  │                      │
│        ▼                  ▼                  ▼                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    REPORT BUILDER                           │   │
│  │         (JSON → Figma Copy Pack / Pencil / PDF)             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Purpose | Cost | Tools |
|-------|---------|------|-------|
| **Collector** | Gather raw data (screenshots, metrics, DOM) | FREE | Playwright, Lighthouse, curl, httpx |
| **Analyzer** | Convert raw data into findings using rules | FREE | Python rules engine |
| **Narrator** | Write human-readable insights + recommendations | ~$0.50-1.00/audit | Claude API |
| **Report Builder** | Format output for Figma/Pencil/PDF | FREE | Python + templates |

---

## 3. Tech Stack Decision

### Final Decision: **Python-Only MVP**

**Rationale:**
- Fastest path to working product for solo developer
- Playwright has excellent Python API
- Lighthouse CLI callable via subprocess
- FastAPI available if dashboard needed later
- All automation libraries (requests, bs4, httpx) native to Python

### Core Stack

```yaml
Runtime:
  - Python 3.11+
  - WSL Ubuntu (local development)
  - Ubuntu VPS (production deployment)

Automation:
  - Playwright (Python) - headless browser, screenshots, DOM extraction
  - Lighthouse CLI - performance metrics, Core Web Vitals
  - curl/httpx - HTTP probing, headers, redirects

Data Processing:
  - Pydantic - schema validation
  - BeautifulSoup4/lxml - HTML parsing

CLI:
  - Typer - command line interface
  - Rich - beautiful terminal output

AI Integration:
  - Anthropic Claude API (claude-sonnet-4-20250514 for cost efficiency)
  - ~1000 tokens per audit narration

Future (Phase 2+):
  - FastAPI - REST API / dashboard backend
  - SQLite/PostgreSQL - audit history storage
  - Docker - containerization for VPS
```

### Why NOT Node.js?

While Node.js has native Playwright and would be better for a SaaS dashboard, the priority is:
1. Get MVP working fast
2. Solo developer efficiency
3. Data analysis/scripting is cleaner in Python

**Later:** If productizing, add a Next.js/React frontend that calls the Python backend via API.

---

## 4. Detailed Component Design

### 4.1 Collector Layer

**Purpose:** Gather evidence without using AI

#### Playwright Snapshot Module
```python
# What it collects:
- Screenshots (desktop + mobile)
- Page title, H1s, H2 hierarchy
- CTA texts and positions
- WhatsApp/contact link detection
- Form fields analysis
- Navigation structure
- Lazy-loaded content (after scroll)
```

#### Lighthouse Module
```python
# What it collects:
- Performance score (mobile + desktop)
- LCP, INP, CLS, TBT, TTFB
- Top 5 opportunities (render-blocking, images, caching)
- Accessibility score
- SEO score
- Best practices score
```

#### HTTP Probe Module
```python
# What it collects:
- Status codes (200/301/404)
- Redirect chains (HTTP→HTTPS, www/non-www)
- Response headers (HSTS, CSP, X-Frame-Options)
- Cache headers
- robots.txt and sitemap.xml
- SSL certificate validity
- Server timing
```

#### Stack Detection Module
```python
# What it collects:
- CMS detection (WordPress, custom, etc.)
- Framework signals
- Analytics pixels (GA4, Meta, etc.)
- Third-party scripts
```

### 4.1.1 Business Logic Analyzer

**Purpose:** Understand the website's purpose and verify features work as intended

Before running technical checks, ProofKit must first understand:
- What type of business is this? (real estate, e-commerce, SaaS, hospitality, etc.)
- What is the primary conversion goal? (inquiries, bookings, purchases, signups)
- What features should exist based on business type?
- Are those features actually working?

#### Business Type Detection
```python
# Auto-detect business type from signals:
BUSINESS_SIGNALS = {
    "real_estate": ["property", "apartment", "villa", "bedroom", "sqft", "price", "location", "floor plan"],
    "ecommerce": ["add to cart", "buy now", "checkout", "product", "shop", "price", "$", "shipping"],
    "saas": ["pricing", "free trial", "sign up", "demo", "features", "integrations", "api"],
    "hospitality": ["book now", "reservation", "check-in", "rooms", "amenities", "guests"],
    "restaurant": ["menu", "order", "delivery", "reservation", "table", "cuisine"],
    "healthcare": ["appointment", "doctor", "patient", "clinic", "services", "insurance"],
    "agency": ["portfolio", "services", "case study", "clients", "contact us", "about us"],
}
```

#### Expected Features by Business Type

| Business Type | Must-Have Features | Should-Have Features |
|---------------|-------------------|---------------------|
| **Real Estate** | Property listings, Inquiry form, Location/map, Price display, Image gallery | Virtual tour, WhatsApp, Floor plans, Payment calculator, Compare units |
| **E-commerce** | Product catalog, Add to cart, Checkout, Search, Price | Filters, Reviews, Wishlist, Stock status, Related products |
| **SaaS** | Pricing page, Sign up/Trial, Feature list, Demo request | Testimonials, Integrations page, Comparison table, FAQ |
| **Hospitality** | Room listings, Booking form, Availability calendar, Amenities | Reviews, Virtual tour, Location map, Special offers |
| **Restaurant** | Menu, Contact/Location, Hours, Reservation/Order | Online ordering, Delivery tracking, Reviews, Gallery |
| **Agency** | Services, Portfolio, Contact form, About | Case studies, Team page, Testimonials, Blog |

#### Feature Verification Tests
```python
# For each expected feature, verify:
class FeatureCheck:
    feature_name: str           # "Inquiry Form"
    expected: bool              # Should this exist based on business type?
    found: bool                 # Was it detected in DOM?
    functional: bool            # Does it actually work? (click/interaction test)
    location: str               # Where on site (homepage, dedicated page, footer)
    accessibility: str          # "above_fold" | "below_fold" | "buried" | "missing"
    evidence: Evidence          # Screenshot, selector, URL
```

#### Business Logic Findings Examples
```python
# Finding: Critical feature missing
Finding(
    id="BIZ-FEAT-001",
    category="CONVERSION",
    severity="P0",
    title="Property inquiry form not found",
    summary="As a real estate website, no property inquiry form was detected on listing pages",
    impact="Visitors cannot express interest in properties - complete conversion blocker",
    recommendation="Add inquiry form to every property page, ideally sticky or above fold",
)

# Finding: Feature exists but broken
Finding(
    id="BIZ-FEAT-002",
    category="CONVERSION",
    severity="P0",
    title="Booking form submission fails",
    summary="The booking form exists but returns error on submission attempt",
    impact="Users cannot complete bookings - 100% conversion loss on this flow",
    recommendation="Debug form handler, check API endpoint, verify email delivery",
)

# Finding: Feature exists but poorly placed
Finding(
    id="BIZ-FEAT-003",
    category="UX",
    severity="P1",
    title="Contact form buried in footer only",
    summary="Primary contact method requires scrolling to page bottom",
    impact="High-intent visitors may leave before discovering how to inquire",
    recommendation="Add sticky CTA or contact option in header/above fold",
)
```

#### CLI Input for Business Context
```bash
# User provides business context for better analysis
proofkit run --url https://example.com \
    --business-type "real_estate" \
    --conversion-goal "property inquiries" \
    --expected-features "inquiry form, whatsapp, virtual tour, price display"

# Or auto-detect mode
proofkit run --url https://example.com --auto-detect
```

#### Business Logic in AI Narration Prompt
```
You are analyzing a {business_type} website.

Primary conversion goal: {conversion_goal}

Expected features for this business type:
{expected_features_list}

Feature verification results:
{feature_check_results}

Based on business logic analysis, highlight:
1. Critical missing features that block conversions
2. Features that exist but don't work properly
3. Features that are poorly positioned/accessible
4. Opportunities based on competitor standards in this industry
```

### 4.1.2 Feature Verification Flow

For each detected/expected feature, ProofKit runs a verification sequence:
```
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE VERIFICATION FLOW                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DETECT                                                      │
│     └─▶ Does the feature exist in DOM?                         │
│         └─▶ Yes: Continue to Step 2                            │
│         └─▶ No: Log as "Missing Feature" (P0/P1)               │
│                                                                 │
│  2. VISIBILITY                                                  │
│     └─▶ Is it visible without scrolling?                       │
│     └─▶ Is it on mobile viewport?                              │
│     └─▶ Is it obscured by other elements?                      │
│         └─▶ Issues: Log as "Poorly Positioned" (P1/P2)         │
│                                                                 │
│  3. INTERACTIVITY                                               │
│     └─▶ Can it be clicked/focused?                             │
│     └─▶ Does hover state exist?                                │
│     └─▶ Is it keyboard accessible?                             │
│         └─▶ Issues: Log as "Interaction Problem" (P1/P2)       │
│                                                                 │
│  4. FUNCTIONALITY (for key features only)                       │
│     └─▶ Click/interact with element                            │
│     └─▶ Did expected outcome occur?                            │
│         - Form: Fields appear, validation works                │
│         - Link: Correct page opens                             │
│         - Button: Modal/action triggers                        │
│         - WhatsApp: wa.me link format correct                  │
│         └─▶ Issues: Log as "Broken Feature" (P0)               │
│                                                                 │
│  5. EVIDENCE                                                    │
│     └─▶ Screenshot the feature                                 │
│     └─▶ Record selector path                                   │
│     └─▶ Note any console errors during interaction             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Features That Get Full Verification (Click Test)

Only test critical conversion features to avoid:
- Accidentally submitting forms
- Triggering rate limits
- Breaking session state
```python
FULL_VERIFICATION_FEATURES = [
    "primary_cta_button",      # Main call-to-action
    "whatsapp_link",           # Verify wa.me format
    "phone_link",              # Verify tel: format
    "email_link",              # Verify mailto: format
    "navigation_menu",         # Verify dropdown/hamburger works
    "search_function",         # Verify search opens/works
    "gallery_lightbox",        # Verify images open
    "video_player",            # Verify video loads
    "map_embed",               # Verify map is interactive
    "chat_widget",             # Verify chat opens
]

# DO NOT click-test:
- Form submit buttons (risk of spam)
- Payment buttons (risk of charges)
- Delete/destructive actions
- External links (track but don't follow)
```


### 4.2 Analyzer Layer

**Purpose:** Convert raw data into structured findings using deterministic rules

#### Finding Schema (Pydantic)
```python
class Finding:
    id: str              # "UX-CTA-001"
    category: Category   # UX | SEO | PERFORMANCE | CONVERSION | SECURITY | MAINTENANCE
    severity: Severity   # P0 | P1 | P2 | P3
    title: str
    summary: str
    impact: str
    recommendation: str
    effort: Effort       # S | M | L
    evidence: List[Evidence]
    tags: List[str]
```

#### Finding Categories (Updated)

| Category | What It Covers | Example Findings |
|----------|---------------|------------------|
| **CONVERSION** | CTAs, forms, contact methods, lead capture | Missing WhatsApp, form too long, no sticky CTA |
| **PERFORMANCE** | Speed, Core Web Vitals, loading | LCP > 4s, render-blocking JS, large images |
| **SEO** | Technical SEO, meta tags, structure | Missing H1, duplicate titles, no sitemap |
| **UX** | Design, navigation, mobile experience | Poor mobile layout, confusing nav, broken links |
| **SECURITY** | SSL, headers, vulnerabilities | Missing HTTPS, weak headers, exposed errors |
| **MAINTENANCE** | Code health, dependencies, monitoring | Outdated libraries, no analytics, broken pages |
| **BUSINESS_LOGIC** | Feature completeness, functionality | Missing expected feature, broken booking flow |
| **ACCESSIBILITY** | WCAG compliance, inclusive design | Missing alt text, poor contrast, no focus states |
| **CONTENT** | Quality, depth, relevance | Thin content, missing FAQ, no testimonials |

#### Rule Categories

| Category | Example Rules |
|----------|---------------|
| **CONVERSION** | Missing WhatsApp CTA, Form has too many fields, No sticky CTA |
| **PERFORMANCE** | LCP > 4s, Render-blocking resources, Large images |
| **SEO** | Missing H1, Multiple H1s, Missing meta description |
| **UX** | Poor mobile viewport, No scroll indication, Broken links |
| **SECURITY** | Missing HTTPS, Weak headers, Exposed server info |
| **MAINTENANCE** | Outdated dependencies, No sitemap, Broken internal links |

### 4.3 Narrator Layer

**Purpose:** Transform findings into persuasive, human-readable content

#### Token Budget Strategy
```
Per Audit Target: ~1500-2500 tokens total

Input to AI:
- Top 10-15 findings (structured)
- Lead's industry (manual input)
- Your offer (redesign + performance + conversion)

Output from AI:
- Executive summary (150 words)
- Key impact statements (5 bullets)
- Prioritized roadmap (quick wins vs long-term)
- "What we can build" concept bullets (for Lovable)
```

#### System Prompt Template
```
You are a website audit analyst for Mimik Creations, a web development agency.

Given these findings from an automated audit, write:
1. Executive Summary (3-4 sentences, focus on business impact)
2. Top 3 Quick Wins (can be fixed in days, high impact)
3. Strategic Priorities (require investment but transform the site)
4. Concept Direction (what a modern redesign could look like)

Industry context: {industry}
Target conversion: {goal} (e.g., "property inquiries", "bookings")

Findings:
{findings_json}

Write in a professional but confident tone. Focus on business outcomes, not technical jargon.
```

### 4.4 Report Builder Layer

**Purpose:** Format output for different destinations

#### Output Formats

| Format | Use Case |
|--------|----------|
| **Figma Copy Pack** | Paste into existing Figma audit template |
| **Markdown Report** | Quick sharing, GitHub, internal docs |
| **JSON Export** | For future dashboard / database storage |
| **Lovable Prompt Pack** | Generate redesign concepts |

---

## 5. Audit Categories (Based on Seven Tides Report)

The audit structure mirrors your existing Figma report:

### 5.1 Web Design & User Experience (UX)
- Visual Design & Brand Alignment
- UI Clarity (buttons, hierarchy, consistency)
- Navigation & Information Architecture
- Mobile & Responsive Experience
- Interaction & Motion (cursor behavior, animations)

### 5.2 Technical SEO & Content
- Performance-Driven SEO Signals (Core Web Vitals)
- On-Page SEO (titles, metas, headings, URLs)
- User Journey Mapping
- Content Gaps & Strategic Opportunities

### 5.3 Lead Generation & Conversion
- CTA Strategy (visibility, placement, messaging)
- Lead Capture Mechanisms (forms, WhatsApp, contact)
- Trust & Reassurance Signals
- Decision Layer (Start Here pathways)

### 5.4 General Maintenance & Site Health
- Infrastructure & Hosting
- Security & Compliance
- Code & Asset Hygiene
- Monitoring & Backup Readiness

---

## 6. Data Flow Example

### Input
```bash
proofkit run --url https://example-lead.com --industry "luxury real estate" --mode fast
```

### Step 1: Collector Output
```
runs/run_20260129_143022/
├── raw/
│   ├── snapshot.json           # Playwright DOM extraction
│   ├── lighthouse_mobile.json  # Lighthouse mobile report
│   ├── lighthouse_desktop.json # Lighthouse desktop report
│   ├── http_probe.json         # Headers, redirects, SSL
│   ├── homepage_desktop.png    # Screenshot
│   └── homepage_mobile.png     # Screenshot
```

### Step 2: Analyzer Output
```json
// findings.json
{
  "findings": [
    {
      "id": "CONV-CTA-001",
      "category": "CONVERSION",
      "severity": "P1",
      "title": "WhatsApp CTA not detected",
      "summary": "No WhatsApp link found on homepage",
      "impact": "Users cannot quickly contact via preferred regional channel",
      "recommendation": "Add visible WhatsApp CTA in header or sticky button",
      "effort": "S",
      "evidence": [{"url": "https://...", "screenshot_path": "..."}]
    },
    // ... more findings
  ],
  "scorecard": {
    "UX": 65,
    "SEO": 72,
    "PERFORMANCE": 34,
    "CONVERSION": 55,
    "SECURITY": 80,
    "MAINTENANCE": 60
  }
}
```

### Step 3: Narrator Output
```json
// narrative.json
{
  "executive_summary": "The website presents a professional aesthetic but suffers from critical performance issues (34/100 mobile performance score) that directly impact lead generation. First-time visitors experience 15+ second load times, with conversion pathways buried beneath navigation friction. Immediate intervention on Core Web Vitals could recover an estimated 30-40% of bounced traffic.",
  
  "quick_wins": [
    "Add WhatsApp CTA to header/sticky position (2-hour fix, high conversion impact)",
    "Convert hero images to WebP format (1-day fix, 3-5s faster load)",
    "Implement response time expectation on forms ('We reply within 2 hours')"
  ],
  
  "strategic_priorities": [
    "Performance overhaul: Target LCP under 2.5s through asset optimization and CDN tuning",
    "Conversion architecture: Add 'Start Here' decision layer for visitor self-segmentation",
    "Trust infrastructure: Integrate reviews, awards, and team visibility on high-intent pages"
  ],
  
  "rebuild_concept": [
    "Modern hero with optimized WebP/AVIF imagery loading in under 2 seconds",
    "Sticky contact bar with WhatsApp, Call, Email options",
    "Property portfolio with intuitive cross-navigation",
    "Trust section with awards, press mentions, and real customer testimonials"
  ]
}
```

### Step 4: Report Builder Output
```
runs/run_20260129_143022/out/
├── report.json           # Complete structured report
├── figma_copy_pack.md    # Ready to paste into Figma
├── lovable_prompts.md    # Prompts for Lovable redesign concept
└── report_summary.md     # Quick overview for internal use
```

---

## 7. Development Roadmap

### Phase 1: MVP (Week 1-2)
**Goal:** First working audit that outputs real evidence

- [ ] Project structure setup
- [ ] Playwright snapshot module (DOM + screenshots + CTA detection)
- [ ] Lighthouse integration (mobile + desktop)
- [ ] Basic HTTP probe (headers, SSL, redirects)
- [ ] Findings analyzer (top 10 rules)
- [ ] Claude API narration (single call)
- [ ] Figma copy pack output
- [ ] CLI command: `proofkit run --url ...`

**Deliverable:** Run audit on any URL, get Figma-ready copy pack

### Phase 2: Pro Audits (Week 3-4)
**Goal:** Deeper analysis, more findings, better evidence

- [ ] Multi-page crawl (15-50 pages)
- [ ] Internal linking analysis
- [ ] Content gap detection
- [ ] Form friction scoring
- [ ] Trust signal inventory
- [ ] Competitor URL comparison (optional input)
- [ ] Priority matrix visualization
- [ ] Extended finding rules (30+ checks)

**Deliverable:** Comprehensive audits matching your existing Figma report quality

### Phase 3: Productization (Month 2)
**Goal:** Reusable, scalable, client-ready

- [ ] Web dashboard (FastAPI + simple HTML/HTMX)
- [ ] Audit history / database storage
- [ ] Industry templates (luxury real estate, SaaS, hospitality)
- [ ] PDF export
- [ ] Lovable prompt pack generation
- [ ] Batch audits (multiple URLs)

### Phase 4: Monetization (Month 3+)
**Goal:** Revenue-generating product

- [ ] Multi-tenant auth
- [ ] Subscription billing
- [ ] White-label option for agencies
- [ ] API access
- [ ] VPS deployment with Docker

---

## 8. Folder Structure

```
~/workspace/Mimik_Proofkit/
├── proofkit/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py              # Typer CLI commands
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── playwright_snapshot.py
│   │   ├── lighthouse.py
│   │   └── http_probe.py
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── rules/
│   │   │   ├── conversion.py
│   │   │   ├── performance.py
│   │   │   ├── seo.py
│   │   │   ├── ux.py
│   │   │   └── security.py
│   │   └── scoring.py
│   ├── narrator/
│   │   ├── __init__.py
│   │   └── claude_narrator.py
│   ├── report_builder/
│   │   ├── __init__.py
│   │   ├── figma_export.py
│   │   ├── markdown_export.py
│   │   └── lovable_prompts.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── finding.py
│   │   └── report.py
│   └── utils/
│       ├── __init__.py
│       └── config.py
├── runs/                        # Audit output directory
├── templates/
│   ├── figma_copy/              # Figma copy templates
│   └── prompts/                 # AI prompt templates
├── tests/
├── pyproject.toml
├── .env                         # API keys (gitignored)
├── .gitignore
└── README.md
```

---

## 9. Key Dependencies

### Python Packages

```toml
# pyproject.toml

[project]
name = "mimik-proofkit"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    # CLI
    "typer>=0.9.0",
    "rich>=13.0.0",
    
    # Data validation
    "pydantic>=2.0.0",
    
    # HTTP
    "requests>=2.31.0",
    "httpx>=0.25.0",
    
    # HTML parsing
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
    
    # Browser automation
    "playwright>=1.40.0",
    
    # AI
    "anthropic>=0.18.0",
    
    # Config
    "python-dotenv>=1.0.0",
]

[project.scripts]
proofkit = "proofkit.cli.main:app"
```

### System Requirements (Ubuntu)

```bash
# WSL Ubuntu / VPS
sudo apt update
sudo apt install -y python3.11 python3.11-venv nodejs npm chromium-browser

# Lighthouse CLI (global)
npm install -g lighthouse

# Playwright browsers
playwright install chromium
```

---

## 10. Configuration

### Environment Variables (.env)

```bash
# AI
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Future integrations
# GOOGLE_SEARCH_CONSOLE_KEY=...
# SENDGRID_API_KEY=...
```

### Config Schema

```python
# proofkit/utils/config.py

class ProofKitConfig:
    # Collector settings
    PLAYWRIGHT_TIMEOUT: int = 60000  # 60 seconds
    LIGHTHOUSE_THROTTLING: str = "mobile"  # or "desktop"
    MAX_PAGES_FAST_MODE: int = 5
    MAX_PAGES_FULL_MODE: int = 50
    
    # Analyzer settings
    SCORE_WEIGHTS: dict = {
        "PERFORMANCE": 0.25,
        "SEO": 0.20,
        "CONVERSION": 0.25,
        "UX": 0.15,
        "SECURITY": 0.10,
        "MAINTENANCE": 0.05,
    }
    
    # Narrator settings
    AI_MODEL: str = "claude-sonnet-4-20250514"
    AI_MAX_TOKENS: int = 1500
    
    # Output settings
    OUTPUT_DIR: str = "runs"
```

---

## 11. CLI Commands

### MVP Commands

```bash
# Basic audit
proofkit run --url https://example.com

# With industry context (for better AI narration)
proofkit run --url https://example.com --industry "luxury real estate"

# Fast mode (homepage only) vs Full mode (crawl 15 pages)
proofkit run --url https://example.com --mode fast
proofkit run --url https://example.com --mode full

# Include Lovable concept prompts
proofkit run --url https://example.com --concept on

# Specify output directory
proofkit run --url https://example.com --output ./client-audits/acme/
```

### Future Commands

```bash
# Compare with competitor
proofkit run --url https://example.com --competitor https://competitor.com

# Batch audit from CSV
proofkit batch --input leads.csv --output ./batch-results/

# View previous audits
proofkit history

# Export specific audit to PDF
proofkit export --run run_20260129_143022 --format pdf
```

---

## 12. API Token Budget Analysis

### Cost Estimation

| Component | Model | Tokens/Audit | Cost/Audit |
|-----------|-------|--------------|------------|
| Narration | claude-sonnet-4-20250514 | ~2000 | ~$0.06 |
| Lovable Prompts | claude-sonnet-4-20250514 | ~800 | ~$0.02 |
| **Total** | | ~2800 | **~$0.08** |

### Monthly Budget Stretch

With $15/month:
- **~180 audits/month** if both narration + Lovable prompts
- **~250 audits/month** if narration only

This is more than enough for lead conversion workflow (~20-30 audits/month typical).

---

## 13. Quality Assurance Checklist

### Per-Audit Validation

- [ ] Screenshots captured (desktop + mobile)
- [ ] Lighthouse scores retrieved
- [ ] HTTP probe completed
- [ ] At least 5 findings generated
- [ ] Scorecard populated
- [ ] Narrative generated
- [ ] Output files created

### Finding Quality Rules

- Every finding must have evidence (URL, screenshot, or metric)
- Severity must match impact (P0 = site-breaking, P1 = conversion-impacting)
- Recommendations must be actionable
- Effort estimates must be realistic

---

## 14. Playwright Click Testing Strategy

### When to Click vs Detect

| Check Type | Method | Reasoning |
|------------|--------|-----------|
| WhatsApp exists | DOM detection | `href` patterns are sufficient |
| CTA visible | Visibility check | `element.is_visible()` |
| CTA clickable | Click test | Verify navigation/modal opens |
| Form submittable | Field count only | Don't submit (spam risk) |
| Links work | DOM + status code | Check `href` + `httpx.get()` |
| Hamburger menu | Click test | Must click to verify content |

### Click Test Implementation

```python
# Only click these elements on key pages (home, contact, property):
CLICK_TEST_ELEMENTS = [
    "primary CTA button",
    "WhatsApp link/button",
    "hamburger menu",
    "contact form submit (don't actually submit)",
]

# Verify after click:
- Did new page/tab open?
- Did modal appear?
- Did URL change?
- Was element blocked by overlay?
```

---

## 15. Integration with Existing Workflow

### Figma Audit Report

Your existing Figma template has these sections:
1. Cover Page
2. Executive Summary
3. Audit Scope & Methodology
4. UX Audit (findings + recommendations)
5. Technical SEO Audit
6. Lead Generation Audit
7. Maintenance Audit
8. Closing Note

**ProofKit output maps directly:**
- `report.json` → All data
- `figma_copy_pack.md` → Copy blocks per section
- Screenshots → Drag into Figma

### Lovable Concept Generation

After audit, generate prompts for Lovable like:
```
"Create a luxury real estate homepage with:
- Modern hero section with WebP background, loads under 2s
- Sticky header with logo, nav, and prominent 'Contact Us' CTA
- Property showcase grid with hover effects
- WhatsApp floating button (bottom-right)
- Trust section with awards, press logos
- Footer with office location map

Style: Minimalist, high-end aesthetic with gold accents
Color palette: #1a1a1a, #ffffff, #c9a962
Font: Playfair Display for headings, Inter for body"
```

---

## 16. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Lighthouse CLI fails on complex sites | Medium | Medium | Fallback to PageSpeed API |
| AI narration costs exceed budget | Low | Medium | Strict token limits, batch processing |
| False positives in findings | Medium | Low | Manual review layer, evidence requirement |
| Playwright blocked by anti-bot | Medium | High | User-agent rotation, proxy support |
| Report output doesn't match Figma template | Low | Medium | Test with real audits, iterate |

---

## 17. Success Metrics

### Phase 1 MVP Success
- [ ] Can audit any public URL in under 5 minutes
- [ ] Generates at least 10 actionable findings
- [ ] Output is directly usable in Figma
- [ ] API cost per audit under $0.10

### Phase 2 Success
- [ ] Audits match quality of manual Seven Tides report
- [ ] Multi-page crawl works reliably
- [ ] Competitor comparison adds value
- [ ] Time to audit: under 10 minutes for full mode

### Business Success
- [ ] Reduces audit preparation time by 70%
- [ ] Increases lead conversion rate (track over 3 months)
- [ ] At least 3 leads converted using ProofKit audits

---



## 18. Next Steps

### Immediate (This Week)

1. **Set up development environment**
   ```bash
   cd ~/workspace/Mimik_Proofkit
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -U pip
   ```

2. **Create project structure**
   ```bash
   mkdir -p proofkit/{cli,collector,analyzer,narrator,report_builder,schemas,utils}
   mkdir -p runs templates/{figma_copy,prompts} tests
   touch proofkit/__init__.py
   ```

3. **Install core dependencies**
   ```bash
   pip install typer rich pydantic requests httpx beautifulsoup4 lxml playwright anthropic python-dotenv
   playwright install chromium
   npm install -g lighthouse
   ```

4. **Create first module: Playwright snapshot**

5. **Test on real URL (e.g., a competitor or cold lead site)**

### Start Coding Session

When you're ready to code, start a new chat with:
> "Let's start coding Mimik ProofKit. I have the foundation doc ready. Begin with [collector/analyzer/narrator/etc.]"

---

## 19. Reference: Seven Tides Audit Findings Map

From your existing Seven Tides audit, these findings should be auto-detectable:

| Finding | Detection Method |
|---------|------------------|
| Custom cursor latency | Playwright: detect custom cursor CSS |
| LCP ~15s | Lighthouse: `largestContentfulPaint` |
| Render-blocking resources | Lighthouse: `render-blocking-resources` |
| Font loading delays | Lighthouse: `font-display` |
| Missing WhatsApp CTA | Playwright: DOM pattern matching |
| Too many form fields | Playwright: count `<input>` in forms |
| No sticky CTA | Playwright: check `position: fixed/sticky` on CTAs |
| Missing H1 | Playwright: `page.locator("h1").count()` |
| No review integration | Playwright: DOM search for Trustpilot/Google Reviews |
| Missing SSL | HTTP probe: certificate check |
| Weak security headers | HTTP probe: header analysis |

---

## 20. Appendix: Useful CLI Commands

```bash
# Check Python version
python3 --version

# Activate virtual environment
source .venv/bin/activate

# Install Playwright browsers
playwright install chromium

# Run Lighthouse manually
lighthouse https://example.com --output json --output-path ./lighthouse.json

# Check SSL certificate
curl -I https://example.com 2>&1 | grep -i "SSL\|HTTP"

# Test HTTP headers
curl -I https://example.com -H "User-Agent: Mozilla/5.0"
```

---

**Document Version:** 1.0  
**Created:** January 2026  
**Ready for:** Development Phase


### Phase 3 Detailed: Advanced Features (Month 2)

#### 3.1 Multi-Page Intelligent Crawl
- Crawl up to 50 pages following internal links
- Prioritize high-value pages: homepage, pricing, contact, product/service pages
- Detect and map site structure automatically
- Identify orphan pages (no internal links pointing to them)

#### 3.2 Competitor Analysis Module
```bash
proofkit run --url https://client.com --competitors "https://competitor1.com,https://competitor2.com"
```
- Compare performance scores side-by-side
- Feature gap analysis (competitor has X, client doesn't)
- Content depth comparison
- CTA strategy comparison
- Generate "Competitor Benchmark Report" section

#### 3.3 Historical Tracking
- Store audit results in SQLite database
- Track improvements over time
- Generate "Progress Report" showing before/after
- Alert when metrics regress

#### 3.4 Industry Templates
Pre-configured audit profiles for:
- Luxury Real Estate (Dubai market focus)
- E-commerce
- SaaS / Tech Startups
- Hospitality & Hotels
- Restaurants & F&B
- Professional Services / Agencies
- Healthcare / Clinics

Each template includes:
- Industry-specific expected features
- Benchmark scores for the industry
- Tailored recommendations
- Industry-specific Lovable prompt templates

#### 3.5 Advanced Form Analysis
- Detect all forms on site
- Count fields and categorize (required vs optional)
- Identify friction points (too many fields, confusing labels)
- Check for validation feedback
- Test submission flow (without actually submitting)
- Verify thank-you page / confirmation exists

#### 3.6 Accessibility Audit (WCAG)
- Color contrast checking
- Alt text presence on images
- Keyboard navigation testing
- Screen reader compatibility signals
- ARIA labels verification
- Focus states on interactive elements

#### 3.7 Content Quality Scoring
- Readability score (Flesch-Kincaid)
- Content length appropriateness per page type
- Keyword density (without stuffing)
- Duplicate content detection across pages
- Missing content opportunities (FAQ, testimonials, etc.)

#### 3.8 Third-Party Integration Audit
Detect and verify:
- Analytics (GA4, GTM, Meta Pixel, etc.)
- Chat widgets (Intercom, Drift, Tawk.to, WhatsApp)
- CRM integrations (HubSpot forms, Salesforce)
- Payment processors (Stripe, PayPal buttons)
- Review widgets (Trustpilot, Google Reviews)
- Map embeds (Google Maps, Mapbox)
- Video embeds (YouTube, Vimeo, Wistia)

#### 3.9 PDF Report Generation
- Professional PDF export matching Figma template style
- Include all screenshots and evidence
- Executive summary on first page
- Branded with Mimik Creations logo
- Shareable link option (upload to cloud storage)

#### 3.10 Scheduled Audits
- Set up recurring audits (weekly/monthly)
- Email notifications when audit completes
- Alert on significant score changes
- Ideal for retainer clients like Seven Tides

#### 3.11 White-Label Configuration
```yaml
# config/whitelabel.yml
brand_name: "Partner Agency Name"
logo_url: "https://..."
primary_color: "#1a1a1a"
contact_email: "audits@partneragency.com"
footer_text: "Powered by Mimik Creations"
```

#### 3.12 API Endpoint (for integrations)
```bash
# REST API for programmatic access
POST /api/v1/audit
{
  "url": "https://example.com",
  "business_type": "real_estate",
  "mode": "full",
  "webhook_url": "https://your-app.com/audit-complete"
}

# Response
{
  "audit_id": "aud_abc123",
  "status": "processing",
  "estimated_time": "180 seconds"
}
```