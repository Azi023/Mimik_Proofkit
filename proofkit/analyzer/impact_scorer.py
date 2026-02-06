"""
Business Impact Scoring

Prioritizes findings by their potential impact on business outcomes,
not just technical severity.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

from proofkit.schemas.finding import Finding
from proofkit.schemas.business import BusinessType
from proofkit.utils.logger import logger


class ImpactCategory(str, Enum):
    """Categories of business impact."""
    REVENUE = "revenue"           # Directly affects sales/conversions
    TRUST = "trust"               # Affects credibility/brand perception
    USABILITY = "usability"       # Affects user experience
    TECHNICAL = "technical"       # Backend/infrastructure
    COMPLIANCE = "compliance"     # Legal/regulatory


@dataclass
class ScoredFinding:
    """Finding with business impact score."""
    finding: Finding
    impact_score: float  # 0-100
    impact_category: ImpactCategory
    revenue_impact: str  # e.g., "Could reduce conversions by 5-10%"
    priority_rank: int = 0


class BusinessImpactScorer:
    """
    Scores findings by business impact, not just technical severity.

    A "High" technical issue that affects a rarely-used admin page
    is less important than a "Medium" issue on the homepage conversion form.
    """

    # Keywords that indicate high business impact
    REVENUE_KEYWORDS = [
        'cta', 'conversion', 'form', 'checkout', 'buy', 'purchase',
        'contact', 'lead', 'submit', 'booking', 'inquiry', 'whatsapp',
        'phone', 'call', 'quote', 'pricing', 'cart', 'order',
    ]

    TRUST_KEYWORDS = [
        'ssl', 'security', 'trust', 'review', 'testimonial', 'certificate',
        'privacy', 'gdpr', 'compliance', 'https', 'credential', 'login',
        'password', 'authentication',
    ]

    USABILITY_KEYWORDS = [
        'navigation', 'mobile', 'responsive', 'accessibility', 'loading',
        'performance', 'speed', 'ux', 'user experience', 'layout', 'scroll',
        'button', 'click', 'tap', 'menu', 'search',
    ]

    COMPLIANCE_KEYWORDS = [
        'gdpr', 'cookie', 'privacy', 'accessibility', 'wcag', 'ada',
        'legal', 'terms', 'copyright',
    ]

    # Page importance weights (multipliers for scores)
    PAGE_WEIGHTS = {
        'homepage': 1.5,
        'home': 1.5,
        '/': 1.5,
        'contact': 1.4,
        'pricing': 1.4,
        'product': 1.3,
        'services': 1.3,
        'checkout': 1.5,
        'cart': 1.4,
        'about': 1.0,
        'blog': 0.7,
        'legal': 0.5,
        'privacy': 0.5,
        'terms': 0.5,
    }

    def __init__(self, business_type: Optional[str] = None):
        """
        Initialize the scorer.

        Args:
            business_type: Business type for context-specific scoring
        """
        self.business_type = business_type
        self._configure_for_business()

    def _configure_for_business(self):
        """Adjust weights based on business type."""
        if not self.business_type:
            return

        bt = self.business_type.lower()

        if bt in ("real_estate", "realestate"):
            self.REVENUE_KEYWORDS.extend([
                'property', 'viewing', 'enquiry', 'portfolio', 'investment',
                'listing', 'mortgage', 'agent', 'tour', 'schedule',
            ])
            self.PAGE_WEIGHTS['property'] = 1.4
            self.PAGE_WEIGHTS['portfolio'] = 1.3
            self.PAGE_WEIGHTS['listings'] = 1.4

        elif bt in ("ecommerce", "e-commerce"):
            self.REVENUE_KEYWORDS.extend([
                'cart', 'product', 'shop', 'add to cart', 'checkout',
                'shipping', 'payment', 'discount', 'promo',
            ])
            self.PAGE_WEIGHTS['product'] = 1.5
            self.PAGE_WEIGHTS['cart'] = 1.5
            self.PAGE_WEIGHTS['shop'] = 1.3

        elif bt in ("saas", "software"):
            self.REVENUE_KEYWORDS.extend([
                'trial', 'demo', 'signup', 'subscribe', 'plan', 'feature',
                'api', 'integration', 'dashboard',
            ])
            self.PAGE_WEIGHTS['pricing'] = 1.5
            self.PAGE_WEIGHTS['features'] = 1.3
            self.PAGE_WEIGHTS['demo'] = 1.4

        elif bt == "hospitality":
            self.REVENUE_KEYWORDS.extend([
                'booking', 'reservation', 'room', 'availability', 'amenities',
                'check-in', 'guest',
            ])
            self.PAGE_WEIGHTS['booking'] = 1.5
            self.PAGE_WEIGHTS['rooms'] = 1.4

        elif bt == "restaurant":
            self.REVENUE_KEYWORDS.extend([
                'menu', 'reservation', 'order', 'delivery', 'table',
                'location', 'hours',
            ])
            self.PAGE_WEIGHTS['menu'] = 1.4
            self.PAGE_WEIGHTS['reservation'] = 1.5
            self.PAGE_WEIGHTS['order'] = 1.5

        elif bt == "healthcare":
            self.REVENUE_KEYWORDS.extend([
                'appointment', 'schedule', 'patient', 'provider', 'doctor',
                'consultation', 'insurance',
            ])
            self.PAGE_WEIGHTS['appointment'] = 1.5
            self.PAGE_WEIGHTS['providers'] = 1.3
            self.PAGE_WEIGHTS['doctors'] = 1.3

    def score_findings(self, findings: List[Finding]) -> List[ScoredFinding]:
        """
        Score all findings and return sorted by impact.

        Args:
            findings: List of findings to score

        Returns:
            List of ScoredFinding objects sorted by impact_score
        """
        scored = []

        for finding in findings:
            score, category, revenue_impact = self._calculate_score(finding)
            scored.append(ScoredFinding(
                finding=finding,
                impact_score=score,
                impact_category=category,
                revenue_impact=revenue_impact,
                priority_rank=0,  # Will be set after sorting
            ))

        # Sort by impact score descending
        scored.sort(key=lambda x: x.impact_score, reverse=True)

        # Assign priority ranks
        for i, sf in enumerate(scored):
            sf.priority_rank = i + 1

        logger.info(f"Scored {len(scored)} findings by business impact")

        return scored

    def _calculate_score(self, finding: Finding) -> Tuple[float, ImpactCategory, str]:
        """
        Calculate impact score for a finding.

        Returns:
            Tuple of (score, category, revenue_impact_description)
        """
        base_score = 50.0
        category = ImpactCategory.TECHNICAL

        # Combine all text for keyword matching
        title_lower = finding.title.lower()
        summary_lower = (finding.summary or '').lower()
        impact_lower = (finding.impact or '').lower()
        text = f"{title_lower} {summary_lower} {impact_lower}"

        # Check for revenue-impacting keywords
        revenue_matches = sum(1 for kw in self.REVENUE_KEYWORDS if kw in text)
        if revenue_matches > 0:
            base_score += revenue_matches * 10
            category = ImpactCategory.REVENUE

        # Check for trust keywords
        trust_matches = sum(1 for kw in self.TRUST_KEYWORDS if kw in text)
        if trust_matches > 0:
            base_score += trust_matches * 8
            if category == ImpactCategory.TECHNICAL:
                category = ImpactCategory.TRUST

        # Check for usability keywords
        ux_matches = sum(1 for kw in self.USABILITY_KEYWORDS if kw in text)
        if ux_matches > 0:
            base_score += ux_matches * 6
            if category == ImpactCategory.TECHNICAL:
                category = ImpactCategory.USABILITY

        # Check for compliance keywords
        compliance_matches = sum(1 for kw in self.COMPLIANCE_KEYWORDS if kw in text)
        if compliance_matches > 0:
            base_score += compliance_matches * 7
            if category == ImpactCategory.TECHNICAL:
                category = ImpactCategory.COMPLIANCE

        # Severity multiplier
        severity = finding.severity
        severity_val = severity.value if hasattr(severity, 'value') else severity
        severity_multipliers = {'P0': 1.5, 'P1': 1.3, 'P2': 1.0, 'P3': 0.7}
        base_score *= severity_multipliers.get(severity_val, 1.0)

        # Page weight multiplier (if we can determine from evidence)
        page_multiplier = self._get_page_multiplier(finding)
        base_score *= page_multiplier

        # Category-specific boost
        finding_category = finding.category.value if hasattr(finding.category, 'value') else finding.category
        if finding_category == 'CONVERSION':
            base_score *= 1.2  # Conversion issues are always important
        elif finding_category == 'SECURITY':
            base_score *= 1.15  # Security is critical

        # Cap at 100
        final_score = min(100, base_score)

        # Generate revenue impact statement
        revenue_impact = self._generate_revenue_impact(category, final_score)

        return final_score, category, revenue_impact

    def _get_page_multiplier(self, finding: Finding) -> float:
        """Determine page importance multiplier from evidence."""
        multiplier = 1.0

        for evidence in finding.evidence:
            url = evidence.url.lower() if evidence.url else ''

            for page_type, weight in self.PAGE_WEIGHTS.items():
                if page_type in url:
                    multiplier = max(multiplier, weight)

        return multiplier

    def _generate_revenue_impact(self, category: ImpactCategory, score: float) -> str:
        """Generate human-readable revenue impact statement."""
        if category == ImpactCategory.REVENUE:
            if score >= 80:
                return "Critical: Could significantly reduce conversions"
            elif score >= 60:
                return "High: May reduce conversions by 5-15%"
            else:
                return "Medium: Could affect some conversion paths"

        elif category == ImpactCategory.TRUST:
            if score >= 80:
                return "Critical: May cause visitors to distrust the site"
            elif score >= 60:
                return "High: Could damage brand perception"
            else:
                return "Medium: May affect perceived credibility"

        elif category == ImpactCategory.USABILITY:
            if score >= 80:
                return "High: Users may abandon due to poor experience"
            elif score >= 60:
                return "Medium: Creates friction in user journey"
            else:
                return "Low: Minor usability inconvenience"

        elif category == ImpactCategory.COMPLIANCE:
            if score >= 80:
                return "Critical: Potential legal/regulatory risk"
            elif score >= 60:
                return "High: Should address for compliance"
            else:
                return "Medium: Consider for best practices"

        return "Low: Limited direct business impact"


def score_by_business_impact(
    findings: List[Finding],
    business_type: Optional[str] = None
) -> List[ScoredFinding]:
    """
    Convenience function for scoring.

    Args:
        findings: List of findings to score
        business_type: Optional business type for context

    Returns:
        List of ScoredFinding objects sorted by impact
    """
    scorer = BusinessImpactScorer(business_type)
    return scorer.score_findings(findings)


def get_top_findings(
    findings: List[Finding],
    count: int = 20,
    business_type: Optional[str] = None
) -> List[Finding]:
    """
    Get the top N findings by business impact.

    Args:
        findings: List of findings to evaluate
        count: Number of top findings to return
        business_type: Optional business type for context

    Returns:
        List of top findings by business impact
    """
    scored = score_by_business_impact(findings, business_type)
    return [sf.finding for sf in scored[:count]]
