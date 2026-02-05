# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mimik ProofKit is an automated website audit QA tool that analyzes websites for UX, SEO, performance, conversion, security, and accessibility issues. It generates AI-powered narratives and actionable findings.

**Status:** MVP planning phase - architecture designed, implementation pending.

## Build & Development Commands

```bash
# Install dependencies (once pyproject.toml is created)
pip install -e ".[dev]"

# Run full audit
proofkit run --url https://example.com --mode fast

# Run specific collectors
proofkit collect --url https://example.com --collector playwright

# Run analyzer on existing data
proofkit analyze --run-dir ./runs/run_YYYYMMDD_HHMMSS

# Generate narrative only
proofkit narrate --run-dir ./runs/run_YYYYMMDD_HHMMSS

# Run tests
pytest tests/
pytest tests/collector/
pytest tests/analyzer/
```

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...          # Required for AI narratives
PROOFKIT_LOG_LEVEL=INFO               # Optional
PROOFKIT_OUTPUT_DIR=./runs            # Optional
```

## Architecture

### Multi-Agent Module Structure

The codebase uses a specialized agent pattern where each module has clear ownership:

| Module | Scope | Location |
|--------|-------|----------|
| Backend Core | CLI, schemas, config, utils | `proofkit/cli/`, `proofkit/schemas/`, `proofkit/utils/`, `proofkit/core/` |
| Collector | Playwright, Lighthouse, HTTP probes | `proofkit/collector/` |
| Analyzer | Rules engine, scoring, findings | `proofkit/analyzer/` |
| Narrator | Claude API integration, prompts | `proofkit/narrator/`, `templates/prompts/` |
| API | FastAPI backend (Phase 2) | `proofkit/api/` |
| Frontend | React dashboard (Phase 3) | `frontend/` |

**Agent documentation:** See `agents/AGENT_*.md` files for detailed specifications of each module.

### Data Flow

```
CLI Input → Collector → RawData (JSON)
                ↓
            Analyzer → List[Finding] (JSON)
                ↓
            Narrator → Narrative (JSON)
                ↓
         Report Builder → Final Output (JSON/HTML)
```

### Shared Schemas

All modules import from `proofkit/schemas/`:

```python
from proofkit.schemas.finding import Finding, Evidence, Severity, Category, Effort
from proofkit.schemas.report import Report, ReportNarrative
from proofkit.schemas.audit import AuditConfig, AuditResult, AuditStatus, AuditMode
from proofkit.schemas.business import BusinessType, FeatureCheck, ExpectedFeatures
```

**Severity levels:** P0 (Critical), P1 (High), P2 (Medium), P3 (Low)

**Categories:** UX, SEO, PERFORMANCE, CONVERSION, SECURITY, MAINTENANCE, BUSINESS_LOGIC, ACCESSIBILITY, CONTENT

### Key Domain Concepts

- **BusinessType:** Auto-detected from content (real_estate, ecommerce, saas, hospitality, restaurant, healthcare, agency, other)
- **FeatureCheck:** Expected features based on business type (e.g., restaurants should have menus, real estate should have property listings)
- **WhatsApp CTA Detection:** Pattern matching for WhatsApp links (common in target market)
- **Lovable Prompts:** Auto-generated design system prompts for redesign recommendations

## Development Phases

| Phase | Modules | Goal |
|-------|---------|------|
| Phase 1 (MVP) | Backend, Collector, Analyzer, Narrator | Working CLI audit |
| Phase 2 (Pro) | + API | REST API for integrations |
| Phase 3 (Product) | + Frontend | Web UI dashboard |

## Code Standards

- Type hints on all functions
- Pydantic models for all data structures
- Custom exceptions hierarchy per module
- Logging via `logging.getLogger(__name__)`
- Keep files under 300 lines
- One primary class per file

## File Ownership

When modifying code, respect module boundaries:
- Collector can import from `schemas/`, `utils/`
- Analyzer can import from `schemas/`, `utils/`, `collector/models.py`
- Narrator can import from `schemas/`, `utils/`
- Never modify files outside your current module's scope
