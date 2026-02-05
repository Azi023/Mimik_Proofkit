# Narrator Agent

## Identity

You are the **Narrator Agent** for Mimik ProofKit. You own the AI integration layer that transforms technical findings into persuasive, business-focused narratives and generates Lovable concept prompts.

## Your Scope

### Files You Own
```
proofkit/narrator/
├── __init__.py              # Narrator class + exports
├── claude_client.py         # Anthropic API wrapper
├── prompts.py               # Prompt templates
├── narrative_builder.py     # Narrative generation logic
├── concept_generator.py     # Lovable prompt generation
└── token_manager.py         # Token budget tracking

templates/prompts/
├── executive_summary.txt    # Executive summary prompt
├── quick_wins.txt           # Quick wins prompt
├── strategic_priorities.txt # Strategic recommendations prompt
├── lovable_concept.txt      # Lovable redesign prompt
└── industry/                # Industry-specific templates
    ├── real_estate.txt
    ├── ecommerce.txt
    ├── saas.txt
    └── hospitality.txt
```

### Files You Import From (Don't Modify)
- `proofkit/schemas/finding.py` - Finding model
- `proofkit/schemas/report.py` - ReportNarrative model
- `proofkit/schemas/business.py` - BusinessType

## Core Responsibilities

### 1. Main Narrator Interface (`proofkit/narrator/__init__.py`)

```python
from typing import List, Optional
from proofkit.schemas.finding import Finding
from proofkit.schemas.report import ReportNarrative
from proofkit.schemas.business import BusinessType

from .claude_client import ClaudeClient
from .narrative_builder import NarrativeBuilder
from .concept_generator import ConceptGenerator
from .token_manager import TokenManager


class Narrator:
    """
    AI-powered narrative generation from audit findings.
    """
    
    def __init__(self):
        self.client = ClaudeClient()
        self.builder = NarrativeBuilder(self.client)
        self.concept_gen = ConceptGenerator(self.client)
        self.token_manager = TokenManager()
    
    def generate(
        self,
        findings: List[Finding],
        business_type: Optional[BusinessType] = None,
        conversion_goal: Optional[str] = None,
        generate_concept: bool = False,
    ) -> ReportNarrative:
        """
        Generate narrative from findings.
        
        Args:
            findings: List of findings from Analyzer
            business_type: Business context for tailored language
            conversion_goal: Primary conversion goal (inquiries, bookings, etc.)
            generate_concept: Whether to generate Lovable concept prompts
            
        Returns:
            ReportNarrative with all narrative content
        """
        # Budget check
        estimated_tokens = self.token_manager.estimate_usage(findings, generate_concept)
        self.token_manager.check_budget(estimated_tokens)
        
        # Prepare findings summary for AI
        findings_summary = self._prepare_findings_summary(findings)
        
        # Generate narrative sections
        executive_summary = self.builder.generate_executive_summary(
            findings_summary,
            business_type,
            conversion_goal,
        )
        
        quick_wins = self.builder.generate_quick_wins(findings_summary)
        
        strategic_priorities = self.builder.generate_strategic_priorities(
            findings_summary,
            business_type,
        )
        
        # Generate concept prompts if requested
        rebuild_concept = []
        lovable_prompts = None
        if generate_concept:
            rebuild_concept = self.concept_gen.generate_concept_bullets(
                findings_summary,
                business_type,
            )
            lovable_prompts = self.concept_gen.generate_lovable_prompt(
                findings_summary,
                business_type,
            )
        
        # Track actual token usage
        self.token_manager.record_usage(self.client.get_last_usage())
        
        return ReportNarrative(
            executive_summary=executive_summary,
            key_wins=quick_wins,
            priority_roadmap=strategic_priorities,
            rebuild_concept=rebuild_concept,
            lovable_prompts=lovable_prompts,
        )
    
    def _prepare_findings_summary(self, findings: List[Finding]) -> str:
        """
        Prepare findings for AI consumption.
        Limit to top findings to save tokens.
        """
        # Take top 15 findings by severity
        top_findings = sorted(
            findings,
            key=lambda f: {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(f.severity, 4)
        )[:15]
        
        summary_lines = []
        for f in top_findings:
            summary_lines.append(
                f"[{f.severity}] {f.category}: {f.title}\n"
                f"  Impact: {f.impact}\n"
                f"  Fix: {f.recommendation}"
            )
        
        return "\n\n".join(summary_lines)
```

### 2. Claude Client (`proofkit/narrator/claude_client.py`)

```python
import anthropic
from typing import Optional, Dict, Any
from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import AIApiError, TokenLimitError


class ClaudeClient:
    """
    Anthropic Claude API wrapper with error handling and usage tracking.
    """
    
    def __init__(self):
        self.config = get_config()
        self.client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
        self.model = self.config.ai_model
        self.max_tokens = self.config.ai_max_tokens
        self._last_usage: Dict[str, int] = {}
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate completion from Claude.
        
        Args:
            system_prompt: System context
            user_prompt: User message
            max_tokens: Override default max tokens
            
        Returns:
            Generated text
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
            )
            
            # Track usage
            self._last_usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
            
            logger.debug(
                f"Claude API: {self._last_usage['input_tokens']} in, "
                f"{self._last_usage['output_tokens']} out"
            )
            
            return response.content[0].text
            
        except anthropic.RateLimitError as e:
            raise AIApiError(f"Rate limit exceeded: {e}")
        except anthropic.APIError as e:
            raise AIApiError(f"API error: {e}")
    
    def get_last_usage(self) -> Dict[str, int]:
        """Get token usage from last request."""
        return self._last_usage.copy()
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough estimate of token count.
        Claude uses ~4 chars per token on average.
        """
        return len(text) // 4
```

### 3. Narrative Builder (`proofkit/narrator/narrative_builder.py`)

```python
from typing import List, Optional
from proofkit.schemas.business import BusinessType
from .claude_client import ClaudeClient
from .prompts import PromptTemplates


class NarrativeBuilder:
    """
    Builds narrative sections from findings using AI.
    """
    
    def __init__(self, client: ClaudeClient):
        self.client = client
        self.templates = PromptTemplates()
    
    def generate_executive_summary(
        self,
        findings_summary: str,
        business_type: Optional[BusinessType] = None,
        conversion_goal: Optional[str] = None,
    ) -> str:
        """
        Generate executive summary for report.
        Target: 3-4 sentences, business-focused.
        """
        system_prompt = self.templates.get_system_prompt("executive_summary")
        
        user_prompt = f"""
Business Type: {business_type.value if business_type else "General business website"}
Conversion Goal: {conversion_goal or "Lead generation / inquiries"}

Audit Findings:
{findings_summary}

Write a concise executive summary (3-4 sentences) that:
1. Leads with the most critical business impact
2. Quantifies the problem where possible
3. Hints at the transformation potential
4. Maintains professional but confident tone

Do NOT use bullet points. Write in flowing prose.
"""
        
        return self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=400,
        )
    
    def generate_quick_wins(self, findings_summary: str) -> List[str]:
        """
        Generate quick wins list.
        Target: 3-5 items that can be fixed in days with high impact.
        """
        system_prompt = self.templates.get_system_prompt("quick_wins")
        
        user_prompt = f"""
Audit Findings:
{findings_summary}

Identify 3-5 "Quick Wins" - fixes that:
- Can be implemented in hours to days (not weeks)
- Have high impact on conversion or user experience
- Don't require major redesign or infrastructure changes

Format each as a single line:
- [Fix description] ([time estimate], [impact level])

Example:
- Add WhatsApp CTA to header (2 hours, high conversion impact)
- Convert hero images to WebP format (1 day, 3-5s faster load)
"""
        
        response = self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
        )
        
        # Parse response into list
        lines = response.strip().split("\n")
        quick_wins = [
            line.strip().lstrip("- •").strip()
            for line in lines
            if line.strip() and not line.startswith("#")
        ]
        
        return quick_wins[:5]
    
    def generate_strategic_priorities(
        self,
        findings_summary: str,
        business_type: Optional[BusinessType] = None,
    ) -> List[str]:
        """
        Generate strategic priority recommendations.
        Target: 3-5 items that require more investment but transform the site.
        """
        system_prompt = self.templates.get_system_prompt("strategic_priorities")
        
        industry_context = ""
        if business_type:
            industry_context = f"Industry: {business_type.value}. Consider industry-specific best practices."
        
        user_prompt = f"""
{industry_context}

Audit Findings:
{findings_summary}

Identify 3-5 Strategic Priorities - investments that:
- Require more effort (weeks, not days)
- Would significantly transform site performance or conversion
- Address root causes, not just symptoms
- Position the business competitively in their industry

Format each as a single line explaining the initiative and expected outcome.
"""
        
        response = self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=600,
        )
        
        # Parse response into list
        lines = response.strip().split("\n")
        priorities = [
            line.strip().lstrip("- •0123456789.").strip()
            for line in lines
            if line.strip() and len(line.strip()) > 20
        ]
        
        return priorities[:5]
```

### 4. Concept Generator (`proofkit/narrator/concept_generator.py`)

```python
from typing import List, Optional
from proofkit.schemas.business import BusinessType
from .claude_client import ClaudeClient
from .prompts import PromptTemplates


class ConceptGenerator:
    """
    Generates Lovable-ready concept prompts and rebuild suggestions.
    """
    
    def __init__(self, client: ClaudeClient):
        self.client = client
        self.templates = PromptTemplates()
    
    def generate_concept_bullets(
        self,
        findings_summary: str,
        business_type: Optional[BusinessType] = None,
    ) -> List[str]:
        """
        Generate concept bullets for "What we can build" section.
        """
        system_prompt = """You are a web design consultant creating concept ideas for a website redesign.
Focus on modern, conversion-optimized design patterns that address the audit findings."""
        
        industry = business_type.value if business_type else "business"
        
        user_prompt = f"""
Based on these audit findings, suggest 4-6 concept improvements:

{findings_summary}

Industry: {industry}

Format as brief, compelling bullets that would excite a client:
- [Improvement]: [Brief benefit]

Focus on:
- Modern UX patterns
- Conversion optimization
- Visual improvements
- Mobile experience
- Speed/performance
"""
        
        response = self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=400,
        )
        
        lines = response.strip().split("\n")
        concepts = [
            line.strip().lstrip("- •").strip()
            for line in lines
            if line.strip() and not line.startswith("#")
        ]
        
        return concepts[:6]
    
    def generate_lovable_prompt(
        self,
        findings_summary: str,
        business_type: Optional[BusinessType] = None,
    ) -> str:
        """
        Generate ready-to-use prompt for Lovable.dev.
        This creates a redesign concept that addresses audit findings.
        """
        system_prompt = """You are an expert at writing prompts for AI website builders like Lovable.dev.
Create detailed, specific prompts that result in professional, modern websites."""
        
        industry = business_type.value if business_type else "business"
        
        # Get industry-specific design guidance
        design_guidance = self._get_design_guidance(business_type)
        
        user_prompt = f"""
Create a Lovable.dev prompt for a {industry} website redesign that addresses these issues:

{findings_summary}

{design_guidance}

The prompt should:
1. Describe the overall design direction (style, mood, aesthetics)
2. Specify the homepage structure (hero, sections, CTA placement)
3. Include specific UI components that fix the audit issues
4. Mention color scheme and typography suggestions
5. Include mobile responsiveness requirements
6. Specify performance considerations (image optimization, lazy loading)

Write a single comprehensive prompt that can be pasted directly into Lovable.
Start with "Create a..." and be specific but not overly technical.
"""
        
        return self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=800,
        )
    
    def _get_design_guidance(self, business_type: Optional[BusinessType]) -> str:
        """Get industry-specific design guidance."""
        guidance = {
            BusinessType.REAL_ESTATE: """
Design guidance for luxury real estate:
- Elegant, minimalist aesthetic with high-quality property imagery
- Dark mode option for premium feel
- Prominent property search/filter
- Large hero images with property highlights
- Trust badges, awards, agent profiles
- WhatsApp and direct contact prominently displayed
- Virtual tour integration
""",
            BusinessType.ECOMMERCE: """
Design guidance for e-commerce:
- Clean product grid with quick-view
- Prominent search and filters
- Clear pricing and availability
- Trust badges (secure payment, returns policy)
- Sticky cart indicator
- Mobile-first checkout flow
""",
            BusinessType.SAAS: """
Design guidance for SaaS:
- Modern, professional aesthetic
- Clear value proposition above fold
- Feature highlights with icons
- Pricing table with comparison
- Social proof (logos, testimonials)
- Strong CTA for free trial/demo
""",
            BusinessType.HOSPITALITY: """
Design guidance for hospitality:
- Immersive imagery showcasing property
- Easy date picker for availability
- Room/suite showcase
- Amenities highlights
- Location and nearby attractions
- Reviews integration
- Direct booking CTA
""",
        }
        
        return guidance.get(business_type, """
Design guidance:
- Clean, modern aesthetic
- Clear navigation
- Prominent CTA above fold
- Mobile-responsive layout
- Fast loading with optimized images
- Trust signals and social proof
""")
```

### 5. Prompt Templates (`proofkit/narrator/prompts.py`)

```python
from pathlib import Path
from typing import Optional


class PromptTemplates:
    """
    Manages prompt templates for AI generation.
    """
    
    TEMPLATES_DIR = Path("templates/prompts")
    
    # Fallback templates if files don't exist
    FALLBACK_TEMPLATES = {
        "executive_summary": """You are a website audit expert at a professional web agency.
Write concise, business-focused content that emphasizes impact and opportunity.
Avoid technical jargon unless necessary. Focus on what matters to business owners:
- Revenue impact
- Customer experience
- Competitive positioning
- Brand perception

Write in a confident, professional tone. Be direct but not alarmist.""",
        
        "quick_wins": """You are a pragmatic web consultant identifying high-impact, low-effort improvements.
Focus on changes that:
- Can be implemented quickly (hours to days)
- Have measurable impact on conversion or user experience
- Don't require major technical overhaul
- Provide visible results to justify further investment""",
        
        "strategic_priorities": """You are a digital strategy consultant creating a transformation roadmap.
Think about:
- Root causes, not just symptoms
- Industry best practices and competitive positioning
- Long-term sustainability and scalability
- Return on investment for each recommendation""",
        
        "lovable_concept": """You are an expert web designer creating concepts for modern, high-converting websites.
Your designs should:
- Follow current design trends (2024-2025)
- Prioritize mobile experience
- Optimize for conversion
- Load fast and perform well
- Reflect the brand's positioning in their market""",
    }
    
    def get_system_prompt(self, template_name: str) -> str:
        """
        Get system prompt for a template.
        Tries file first, falls back to built-in.
        """
        # Try loading from file
        template_path = self.TEMPLATES_DIR / f"{template_name}.txt"
        if template_path.exists():
            return template_path.read_text()
        
        # Fall back to built-in
        return self.FALLBACK_TEMPLATES.get(
            template_name,
            "You are a helpful website audit assistant."
        )
    
    def get_industry_template(self, business_type: str) -> Optional[str]:
        """Get industry-specific template if available."""
        industry_path = self.TEMPLATES_DIR / "industry" / f"{business_type}.txt"
        if industry_path.exists():
            return industry_path.read_text()
        return None
```

### 6. Token Manager (`proofkit/narrator/token_manager.py`)

```python
from typing import Dict, List
from proofkit.schemas.finding import Finding
from proofkit.utils.config import get_config
from proofkit.utils.logger import logger
from proofkit.utils.exceptions import TokenLimitError


class TokenManager:
    """
    Manages AI token budget to stay within cost limits.
    """
    
    # Estimated tokens per section
    SECTION_ESTIMATES = {
        "executive_summary": 500,
        "quick_wins": 600,
        "strategic_priorities": 700,
        "concept_bullets": 500,
        "lovable_prompt": 1000,
    }
    
    # Cost per 1K tokens (approximate for Claude Sonnet)
    COST_PER_1K_INPUT = 0.003
    COST_PER_1K_OUTPUT = 0.015
    
    def __init__(self, monthly_budget: float = 15.0):
        self.monthly_budget = monthly_budget
        self.monthly_usage: Dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
        }
    
    def estimate_usage(
        self,
        findings: List[Finding],
        generate_concept: bool = False,
    ) -> int:
        """
        Estimate tokens needed for this audit.
        """
        # Input: findings summary
        findings_text = sum(
            len(f.title) + len(f.impact) + len(f.recommendation)
            for f in findings[:15]
        )
        input_estimate = findings_text // 4  # ~4 chars per token
        
        # Output: all sections
        output_estimate = (
            self.SECTION_ESTIMATES["executive_summary"] +
            self.SECTION_ESTIMATES["quick_wins"] +
            self.SECTION_ESTIMATES["strategic_priorities"]
        )
        
        if generate_concept:
            output_estimate += (
                self.SECTION_ESTIMATES["concept_bullets"] +
                self.SECTION_ESTIMATES["lovable_prompt"]
            )
        
        return input_estimate + output_estimate
    
    def check_budget(self, estimated_tokens: int):
        """
        Check if we have budget for this request.
        Raises TokenLimitError if over budget.
        """
        estimated_cost = self._estimate_cost(estimated_tokens)
        remaining_budget = self._get_remaining_budget()
        
        if estimated_cost > remaining_budget:
            raise TokenLimitError(
                f"Estimated cost ${estimated_cost:.2f} exceeds remaining "
                f"budget ${remaining_budget:.2f}. Try reducing findings or "
                f"disabling concept generation."
            )
        
        logger.debug(
            f"Token budget check: ~{estimated_tokens} tokens, "
            f"~${estimated_cost:.3f} estimated"
        )
    
    def record_usage(self, usage: Dict[str, int]):
        """Record actual token usage after API call."""
        self.monthly_usage["input_tokens"] += usage.get("input_tokens", 0)
        self.monthly_usage["output_tokens"] += usage.get("output_tokens", 0)
        
        logger.info(
            f"Token usage: {usage.get('input_tokens', 0)} in, "
            f"{usage.get('output_tokens', 0)} out. "
            f"Monthly total: {self.monthly_usage['input_tokens']} in, "
            f"{self.monthly_usage['output_tokens']} out"
        )
    
    def _estimate_cost(self, total_tokens: int) -> float:
        """Estimate cost for tokens (assumes 1:1 input:output ratio)."""
        half = total_tokens // 2
        return (
            (half / 1000) * self.COST_PER_1K_INPUT +
            (half / 1000) * self.COST_PER_1K_OUTPUT
        )
    
    def _get_remaining_budget(self) -> float:
        """Calculate remaining monthly budget."""
        used = (
            (self.monthly_usage["input_tokens"] / 1000) * self.COST_PER_1K_INPUT +
            (self.monthly_usage["output_tokens"] / 1000) * self.COST_PER_1K_OUTPUT
        )
        return self.monthly_budget - used
    
    def get_usage_report(self) -> Dict:
        """Get usage statistics."""
        used_cost = (
            (self.monthly_usage["input_tokens"] / 1000) * self.COST_PER_1K_INPUT +
            (self.monthly_usage["output_tokens"] / 1000) * self.COST_PER_1K_OUTPUT
        )
        
        return {
            "input_tokens": self.monthly_usage["input_tokens"],
            "output_tokens": self.monthly_usage["output_tokens"],
            "total_tokens": sum(self.monthly_usage.values()),
            "estimated_cost": round(used_cost, 3),
            "remaining_budget": round(self.monthly_budget - used_cost, 2),
            "budget_used_percent": round((used_cost / self.monthly_budget) * 100, 1),
        }
```

## Testing Requirements

```python
# tests/narrator/
├── conftest.py              # Mock Claude client
├── test_narrator.py         # Integration tests
├── test_narrative_builder.py
├── test_concept_generator.py
├── test_token_manager.py
```

## Your First Tasks (Phase 1 MVP)

1. [ ] Create `proofkit/narrator/__init__.py` with Narrator class
2. [ ] Implement `claude_client.py` with error handling
3. [ ] Implement `prompts.py` with fallback templates
4. [ ] Implement `narrative_builder.py` - executive summary + quick wins
5. [ ] Implement `token_manager.py` - budget tracking
6. [ ] Implement `concept_generator.py` - Lovable prompts
7. [ ] Create template files in `templates/prompts/`
8. [ ] Write tests with mocked Claude responses
9. [ ] Test with real findings from Analyzer

## Interface Contract

### Input (from Analyzer Agent)
```python
from proofkit.schemas.finding import Finding

findings: List[Finding]  # Sorted by severity
```

### Output (to Report Builder)
```python
from proofkit.schemas.report import ReportNarrative

# You return:
narrative: ReportNarrative
  - executive_summary: str
  - key_wins: List[str]
  - priority_roadmap: List[str]
  - rebuild_concept: List[str]
  - lovable_prompts: Optional[str]
```

## Token Budget Guidelines

**Target: ~$0.08 per audit**

| Section | Max Tokens | Estimated Cost |
|---------|------------|----------------|
| Executive Summary | 400 | $0.02 |
| Quick Wins | 500 | $0.02 |
| Strategic Priorities | 600 | $0.02 |
| Concept Bullets | 400 | $0.01 |
| Lovable Prompt | 800 | $0.02 |
| **Total** | **~2700** | **~$0.08** |

With $15/month budget: **~180 full audits** possible.
