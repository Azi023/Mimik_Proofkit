# Mimik ProofKit - Multi-Agent Development Setup

## Overview

This project uses a multi-agent architecture where specialized agents work on different parts of the system. Each agent has clear responsibilities, interfaces, and code ownership.

## Agent Structure

```
agents/
├── CLAUDE.md           # Main orchestrator (read this first)
├── AGENT_BACKEND.md    # CLI, schemas, config, utils
├── AGENT_COLLECTOR.md  # Playwright, Lighthouse, HTTP probes
├── AGENT_ANALYZER.md   # Rules engine, scoring, findings
├── AGENT_NARRATOR.md   # AI narration, Lovable prompts
├── AGENT_API.md        # FastAPI backend (Phase 2)
└── AGENT_FRONTEND.md   # React dashboard (Phase 3)
```

## Phase Activation

| Phase | Active Agents | Goal |
|-------|---------------|------|
| **Phase 1 (MVP)** | Backend, Collector, Analyzer, Narrator | Working CLI audit |
| **Phase 2 (API)** | + API Agent | REST API for integrations |
| **Phase 3 (Dashboard)** | + Frontend Agent | Web UI for audits |

## How to Use These Agents

### Option 1: Sequential Development (Recommended for Solo)

Work through agents in order:

```bash
# Step 1: Backend Core
# Run Claude Code and say:
"Read agents/AGENT_BACKEND.md and complete all Phase 1 tasks"

# Step 2: Collector
"Read agents/AGENT_COLLECTOR.md and implement the collector module"

# Step 3: Analyzer
"Read agents/AGENT_ANALYZER.md and implement the analyzer module"

# Step 4: Narrator
"Read agents/AGENT_NARRATOR.md and implement the narrator module"
```

### Option 2: Parallel Development (With Multiple Terminals)

Run multiple Claude Code sessions, each focused on one agent:

**Terminal 1 - Backend:**
```bash
claude
> "You are the Backend Agent. Read agents/AGENT_BACKEND.md. Focus only on your scope."
```

**Terminal 2 - Collector:**
```bash
claude
> "You are the Collector Agent. Read agents/AGENT_COLLECTOR.md. Focus only on your scope."
```

### Option 3: Task-Based Assignment

Give specific tasks referencing agent docs:

```bash
"Referring to agents/AGENT_COLLECTOR.md, implement the Playwright snapshot module with WhatsApp detection"

"Referring to agents/AGENT_ANALYZER.md, implement the conversion rules for CTA analysis"
```

## File Ownership Rules

**Critical:** Agents must NOT modify files outside their scope.

| Agent | Owns | Can Import From |
|-------|------|-----------------|
| Backend | `cli/`, `schemas/`, `utils/`, `core/` | - |
| Collector | `collector/` | `schemas/`, `utils/` |
| Analyzer | `analyzer/` | `schemas/`, `utils/`, `collector/models.py` |
| Narrator | `narrator/`, `templates/prompts/` | `schemas/`, `utils/` |
| API | `api/` | All above |
| Frontend | `frontend/` | API responses only |

## Interface Contracts

### Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   CLI (Backend)                                              │
│      │                                                       │
│      ▼                                                       │
│   Collector ──────▶ RawData (JSON)                          │
│      │                  │                                    │
│      │                  ▼                                    │
│      │            Analyzer ──────▶ List[Finding]            │
│      │                  │              │                     │
│      │                  │              ▼                     │
│      │                  │         Narrator ──▶ Narrative    │
│      │                  │              │                     │
│      │                  ▼              ▼                     │
│      └────────────▶ Report Builder ──────▶ Final Report     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Shared Types (from `proofkit/schemas/`)

All agents import these schemas:

```python
# Every agent needs these
from proofkit.schemas.finding import Finding, Evidence, Severity, Category
from proofkit.schemas.report import Report, ReportNarrative
from proofkit.schemas.audit import AuditConfig, AuditResult
from proofkit.schemas.business import BusinessType, FeatureCheck
```

## Development Order (Phase 1)

```
Week 1:
├── Day 1-2: Backend Agent (schemas, config, CLI skeleton)
├── Day 3-4: Collector Agent (Playwright, Lighthouse)
├── Day 5: Collector Agent (HTTP probe, stack detection)

Week 2:
├── Day 1-2: Analyzer Agent (rules engine, top 10 rules)
├── Day 3: Analyzer Agent (scoring)
├── Day 4: Narrator Agent (Claude client, prompts)
├── Day 5: Integration + Testing
```

## Testing Strategy

Each agent maintains its own tests:

```
tests/
├── conftest.py              # Shared fixtures
├── test_schemas.py          # Backend
├── test_config.py           # Backend
├── collector/
│   ├── test_playwright.py   # Collector
│   ├── test_lighthouse.py   # Collector
│   └── test_http_probe.py   # Collector
├── analyzer/
│   ├── test_rules.py        # Analyzer
│   └── test_scoring.py      # Analyzer
├── narrator/
│   └── test_narrator.py     # Narrator (mocked Claude)
└── integration/
    └── test_full_audit.py   # End-to-end
```

## Code Quality Standards

All agents follow these standards:

1. **Type hints everywhere**
2. **Pydantic for data models**
3. **Docstrings for public functions**
4. **Error handling with custom exceptions**
5. **Logging at appropriate levels**
6. **Tests for critical paths**

## Quick Start for Claude Code

Copy this into your Mimik_Proofkit folder and run `/init`:

```bash
# Copy all agent files
cp -r mimik-proofkit-agents/* ~/workspace/Mimik_Proofkit/
```

Then in Claude Code:

```
/init

Read CLAUDE.md first, then start with the Backend Agent tasks from agents/AGENT_BACKEND.md
```

## Troubleshooting

### "Agent modified wrong file"
Each agent doc has a "Files You Own" section. Remind Claude of its scope:
```
"Remember, as the Collector Agent you only modify files in proofkit/collector/"
```

### "Interface mismatch between agents"
All shared interfaces are in `proofkit/schemas/`. If there's a mismatch:
```
"Check proofkit/schemas/finding.py for the correct Finding model structure"
```

### "Agent doesn't have context"
Start fresh sessions with the agent doc:
```
"Read agents/AGENT_COLLECTOR.md completely before proceeding"
```

## Files to Copy to Your Project

1. `CLAUDE.md` → `~/workspace/Mimik_Proofkit/CLAUDE.md`
2. `agents/` folder → `~/workspace/Mimik_Proofkit/agents/`
3. Keep `MIMIK_PROOFKIT_FOUNDATION.md` as reference

Good luck building! 🚀
