"""Business type detection from page content."""

import re
from typing import Dict, List, Optional, Tuple

from proofkit.utils.logger import logger
from proofkit.schemas.business import BusinessType

from .models import SnapshotData, BusinessSignals


class BusinessDetector:
    """Detect business type from page content using keyword analysis."""

    # Keywords for each business type (weighted by importance)
    BUSINESS_KEYWORDS = {
        BusinessType.REAL_ESTATE: {
            "high": [
                "property", "properties", "real estate", "realty",
                "for sale", "for rent", "apartment", "apartments",
                "villa", "villas", "condo", "townhouse", "duplex",
                "bedroom", "bedrooms", "sqft", "sq ft", "square feet",
                "floor plan", "listing", "listings", "mls",
            ],
            "medium": [
                "location", "neighborhood", "mortgage", "financing",
                "agent", "broker", "open house", "virtual tour",
                "price", "rent", "lease", "buy", "sell",
            ],
            "low": [
                "home", "house", "land", "lot", "commercial",
                "residential", "investment", "roi",
            ],
        },
        BusinessType.ECOMMERCE: {
            "high": [
                "add to cart", "add to bag", "buy now", "shop now",
                "checkout", "shopping cart", "cart", "basket",
                "product", "products", "shop", "store",
            ],
            "medium": [
                "shipping", "delivery", "free shipping", "returns",
                "stock", "in stock", "out of stock", "quantity",
                "size", "color", "variant", "sku",
            ],
            "low": [
                "price", "sale", "discount", "offer", "deal",
                "wishlist", "favorites", "compare",
            ],
        },
        BusinessType.SAAS: {
            "high": [
                "pricing", "plans", "free trial", "start free",
                "sign up", "get started", "demo", "request demo",
                "software", "platform", "solution", "tool",
            ],
            "medium": [
                "features", "integrations", "api", "dashboard",
                "analytics", "automation", "workflow", "collaboration",
                "team", "enterprise", "business plan",
            ],
            "low": [
                "cloud", "saas", "subscription", "monthly", "annually",
                "per user", "per seat", "upgrade",
            ],
        },
        BusinessType.HOSPITALITY: {
            "high": [
                "book now", "reserve", "reservation", "booking",
                "hotel", "resort", "accommodation", "stay",
                "room", "rooms", "suite", "guest",
            ],
            "medium": [
                "check-in", "check-out", "amenities", "facilities",
                "spa", "pool", "restaurant", "bar", "concierge",
                "availability", "rates", "per night",
            ],
            "low": [
                "travel", "vacation", "holiday", "destination",
                "experience", "luxury", "boutique",
            ],
        },
        BusinessType.RESTAURANT: {
            "high": [
                "menu", "order online", "order now", "delivery",
                "takeout", "takeaway", "dine-in", "reservation",
                "table", "book a table", "restaurant",
            ],
            "medium": [
                "cuisine", "dish", "dishes", "food", "meal",
                "lunch", "dinner", "breakfast", "brunch",
                "appetizer", "entree", "dessert", "drinks",
            ],
            "low": [
                "chef", "kitchen", "fresh", "organic", "local",
                "specials", "happy hour", "catering",
            ],
        },
        BusinessType.HEALTHCARE: {
            "high": [
                "appointment", "book appointment", "schedule",
                "doctor", "physician", "clinic", "hospital",
                "patient", "medical", "healthcare", "health care",
            ],
            "medium": [
                "services", "treatment", "diagnosis", "specialist",
                "emergency", "urgent care", "primary care",
                "insurance", "telehealth", "telemedicine",
            ],
            "low": [
                "health", "wellness", "care", "medicine",
                "symptoms", "conditions", "therapy",
            ],
        },
        BusinessType.AGENCY: {
            "high": [
                "portfolio", "case study", "case studies", "our work",
                "clients", "agency", "studio", "creative",
                "services", "solutions",
            ],
            "medium": [
                "design", "development", "marketing", "branding",
                "digital", "web design", "app development",
                "strategy", "consulting", "team",
            ],
            "low": [
                "project", "campaign", "results", "approach",
                "process", "expertise", "industry",
            ],
        },
    }

    # Feature indicators for each business type
    FEATURE_INDICATORS = {
        BusinessType.REAL_ESTATE: [
            "property_search", "map_view", "price_filter", "bedroom_filter",
            "virtual_tour", "mortgage_calculator", "inquiry_form",
        ],
        BusinessType.ECOMMERCE: [
            "product_grid", "add_to_cart_button", "shopping_cart",
            "product_filter", "size_selector", "checkout_button",
        ],
        BusinessType.SAAS: [
            "pricing_table", "feature_list", "comparison_table",
            "signup_form", "demo_request", "testimonials",
        ],
        BusinessType.HOSPITALITY: [
            "booking_widget", "date_picker", "room_gallery",
            "amenity_list", "availability_calendar", "rate_display",
        ],
        BusinessType.RESTAURANT: [
            "menu_section", "order_button", "reservation_widget",
            "delivery_options", "location_hours", "menu_categories",
        ],
        BusinessType.HEALTHCARE: [
            "appointment_scheduler", "doctor_profiles", "service_list",
            "patient_portal", "insurance_info", "contact_form",
        ],
        BusinessType.AGENCY: [
            "portfolio_grid", "case_study_section", "service_cards",
            "team_section", "client_logos", "contact_form",
        ],
    }

    # Keyword weights
    WEIGHTS = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    def detect(self, snapshot: SnapshotData) -> BusinessSignals:
        """
        Detect business type from snapshot data.

        Args:
            snapshot: SnapshotData from Playwright collector

        Returns:
            BusinessSignals with detected type and confidence
        """
        logger.info("Detecting business type")

        # Combine text content from all pages
        text_content = self._extract_text_content(snapshot)

        # Score each business type
        scores = self._calculate_scores(text_content)

        # Find best match
        if not scores:
            return BusinessSignals()

        best_type, best_score = max(scores.items(), key=lambda x: x[1])
        total_score = sum(scores.values())

        # Calculate confidence
        confidence = best_score / total_score if total_score > 0 else 0

        # Get matched keywords for the best type
        keyword_matches = self._get_keyword_matches(text_content, best_type)

        # Detect feature indicators
        feature_indicators = self._detect_features(snapshot, best_type)

        # Adjust confidence based on feature presence
        if feature_indicators:
            confidence = min(1.0, confidence + 0.1 * len(feature_indicators))

        # Only report if confidence is above threshold
        if confidence < 0.3:
            return BusinessSignals(
                keyword_matches={bt.value: self._get_keyword_matches(text_content, bt) for bt in scores.keys()},
            )

        return BusinessSignals(
            detected_type=best_type.value,
            confidence=round(confidence, 2),
            keyword_matches={best_type.value: keyword_matches},
            feature_indicators=feature_indicators,
            industry_signals=self._get_industry_signals(text_content),
        )

    def detect_from_text(self, text: str) -> Tuple[Optional[str], float]:
        """
        Simple detection from text content.

        Args:
            text: Text content to analyze

        Returns:
            Tuple of (business_type, confidence)
        """
        text_lower = text.lower()
        scores = self._calculate_scores(text_lower)

        if not scores:
            return None, 0.0

        best_type, best_score = max(scores.items(), key=lambda x: x[1])
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0

        if confidence < 0.3:
            return None, confidence

        return best_type.value, round(confidence, 2)

    def _extract_text_content(self, snapshot: SnapshotData) -> str:
        """Extract all text content from snapshot."""
        text_parts = []

        for page in snapshot.pages:
            # Add title
            if page.title:
                text_parts.append(page.title)

            # Add headings
            for level, headings in page.headings.items():
                text_parts.extend(headings)

            # Add CTA text
            for cta in page.ctas:
                text_parts.append(cta.text)

            # Add navigation links
            if page.navigation:
                for link in page.navigation.links:
                    text_parts.append(link.get("text", ""))

            # Add meta description
            if page.meta_tags.get("description"):
                text_parts.append(page.meta_tags["description"])

        return " ".join(text_parts).lower()

    def _calculate_scores(self, text: str) -> Dict[BusinessType, float]:
        """Calculate scores for each business type."""
        scores = {}

        for business_type, keywords_by_weight in self.BUSINESS_KEYWORDS.items():
            score = 0

            for weight_level, keywords in keywords_by_weight.items():
                weight = self.WEIGHTS[weight_level]

                for keyword in keywords:
                    # Count occurrences
                    count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE))
                    if count > 0:
                        # Diminishing returns for repeated keywords
                        score += weight * min(count, 3)

            if score > 0:
                scores[business_type] = score

        return scores

    def _get_keyword_matches(self, text: str, business_type: BusinessType) -> List[str]:
        """Get list of matched keywords for a business type."""
        matches = []
        keywords_by_weight = self.BUSINESS_KEYWORDS.get(business_type, {})

        for weight_level, keywords in keywords_by_weight.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                    matches.append(keyword)

        return matches[:20]  # Limit

    def _detect_features(self, snapshot: SnapshotData, business_type: BusinessType) -> List[str]:
        """Detect feature indicators for a business type."""
        found_features = []
        expected_features = self.FEATURE_INDICATORS.get(business_type, [])

        for page in snapshot.pages:
            # Check for forms
            if page.forms:
                if business_type in [BusinessType.REAL_ESTATE, BusinessType.HEALTHCARE]:
                    if any(f.has_phone_field for f in page.forms):
                        found_features.append("inquiry_form")
                if business_type == BusinessType.SAAS:
                    if any(f.has_email_field for f in page.forms):
                        found_features.append("signup_form")

            # Check for CTAs
            cta_texts = [cta.text.lower() for cta in page.ctas]

            if business_type == BusinessType.ECOMMERCE:
                if any("cart" in t or "buy" in t for t in cta_texts):
                    found_features.append("add_to_cart_button")

            if business_type == BusinessType.HOSPITALITY:
                if any("book" in t or "reserve" in t for t in cta_texts):
                    found_features.append("booking_widget")

            if business_type == BusinessType.RESTAURANT:
                if any("order" in t or "menu" in t for t in cta_texts):
                    found_features.append("order_button")

        return list(set(found_features))

    def _get_industry_signals(self, text: str) -> List[str]:
        """Get general industry signals from text."""
        signals = []

        industry_keywords = {
            "b2b": ["enterprise", "business", "b2b", "companies", "organizations"],
            "b2c": ["consumers", "customers", "individuals", "personal"],
            "local": ["near me", "local", "nearby", "location", "visit us"],
            "global": ["worldwide", "international", "global", "countries"],
            "premium": ["luxury", "premium", "exclusive", "high-end"],
            "budget": ["affordable", "cheap", "budget", "discount", "save"],
        }

        for signal, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    signals.append(signal)
                    break

        return list(set(signals))
