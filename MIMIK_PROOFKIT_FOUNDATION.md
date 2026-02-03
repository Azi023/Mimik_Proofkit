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
