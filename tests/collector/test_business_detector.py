"""Tests for business type detector."""

import pytest

from proofkit.collector.business_detector import BusinessDetector
from proofkit.collector.models import (
    SnapshotData,
    PageSnapshot,
    CTAInfo,
    FormInfo,
    NavigationInfo,
)
from proofkit.schemas.business import BusinessType


class TestBusinessDetector:
    def test_init(self):
        detector = BusinessDetector()
        assert detector is not None
        assert len(detector.BUSINESS_KEYWORDS) > 0
        assert BusinessType.REAL_ESTATE in detector.BUSINESS_KEYWORDS


class TestKeywordScoring:
    def test_calculate_scores_real_estate(self):
        detector = BusinessDetector()
        text = """
        Browse our luxury property listings. Find your perfect 3 bedroom apartment
        or villa for sale. View floor plans and schedule a virtual tour.
        Properties starting from $200,000. Contact our real estate agents today.
        """
        scores = detector._calculate_scores(text.lower())

        assert BusinessType.REAL_ESTATE in scores
        assert scores[BusinessType.REAL_ESTATE] > 0
        # Real estate should have highest score
        best_type = max(scores, key=scores.get)
        assert best_type == BusinessType.REAL_ESTATE

    def test_calculate_scores_ecommerce(self):
        detector = BusinessDetector()
        text = """
        Shop our latest products. Add to cart and checkout securely.
        Free shipping on orders over $50. Browse our product catalog.
        In stock and ready to ship. Best deals and discounts.
        """
        scores = detector._calculate_scores(text.lower())

        assert BusinessType.ECOMMERCE in scores
        best_type = max(scores, key=scores.get)
        assert best_type == BusinessType.ECOMMERCE

    def test_calculate_scores_saas(self):
        detector = BusinessDetector()
        text = """
        Start your free trial today. View our pricing plans.
        Request a demo to see our platform in action.
        Features include API integrations, team collaboration,
        and workflow automation. Sign up for the business plan.
        """
        scores = detector._calculate_scores(text.lower())

        assert BusinessType.SAAS in scores
        best_type = max(scores, key=scores.get)
        assert best_type == BusinessType.SAAS

    def test_calculate_scores_restaurant(self):
        detector = BusinessDetector()
        text = """
        View our menu and order online for delivery or takeout.
        Book a table for dinner. Our cuisine features fresh
        local ingredients. Daily lunch specials available.
        """
        scores = detector._calculate_scores(text.lower())

        assert BusinessType.RESTAURANT in scores
        best_type = max(scores, key=scores.get)
        assert best_type == BusinessType.RESTAURANT

    def test_calculate_scores_hospitality(self):
        detector = BusinessDetector()
        text = """
        Book now and reserve your room at our luxury resort.
        Check-in is at 3pm. Amenities include spa, pool, and restaurant.
        View availability and rates per night. Guest services available.
        """
        scores = detector._calculate_scores(text.lower())

        assert BusinessType.HOSPITALITY in scores
        best_type = max(scores, key=scores.get)
        assert best_type == BusinessType.HOSPITALITY

    def test_calculate_scores_healthcare(self):
        detector = BusinessDetector()
        text = """
        Schedule your appointment with our doctors. Patient portal
        available for medical records. Clinic services include
        primary care and specialist consultations. Insurance accepted.
        """
        scores = detector._calculate_scores(text.lower())

        assert BusinessType.HEALTHCARE in scores
        best_type = max(scores, key=scores.get)
        assert best_type == BusinessType.HEALTHCARE

    def test_calculate_scores_agency(self):
        detector = BusinessDetector()
        text = """
        View our portfolio and case studies. Our creative agency
        offers design, development, and marketing services.
        Meet our team and see client testimonials.
        """
        scores = detector._calculate_scores(text.lower())

        assert BusinessType.AGENCY in scores
        best_type = max(scores, key=scores.get)
        assert best_type == BusinessType.AGENCY


class TestDetectFromText:
    def test_detect_real_estate(self):
        detector = BusinessDetector()
        text = "property listings bedroom villa for sale sqft floor plan"
        business_type, confidence = detector.detect_from_text(text)

        assert business_type == "real_estate"
        assert confidence > 0.3

    def test_detect_ecommerce(self):
        detector = BusinessDetector()
        text = "add to cart checkout shop product buy now shipping"
        business_type, confidence = detector.detect_from_text(text)

        assert business_type == "ecommerce"
        assert confidence > 0.3

    def test_detect_low_confidence(self):
        detector = BusinessDetector()
        text = "welcome to our website contact us for more information"
        business_type, confidence = detector.detect_from_text(text)

        # Should have low confidence or None
        assert confidence < 0.5


class TestDetectFromSnapshot:
    def test_detect_from_snapshot_real_estate(self, sample_html_real_estate):
        detector = BusinessDetector()
        snapshot = SnapshotData(
            url="https://example.com",
            pages=[
                PageSnapshot(
                    url="https://example.com",
                    title="Luxury Properties - Find Your Dream Home",
                    headings={
                        "h1": ["Find Your Perfect Property"],
                        "h2": ["Featured Listings"],
                        "h3": ["3 Bedroom Villa - $500,000"],
                    },
                    ctas=[
                        CTAInfo(text="Inquire Now", type="link"),
                        CTAInfo(text="Contact via WhatsApp", type="link"),
                    ],
                    forms=[
                        FormInfo(
                            field_count=3,
                            has_email_field=True,
                            has_phone_field=True,
                        )
                    ],
                    navigation=NavigationInfo(
                        links=[
                            {"text": "Home", "href": "/"},
                            {"text": "Properties", "href": "/properties"},
                            {"text": "Contact", "href": "/contact"},
                        ]
                    ),
                    meta_tags={"description": "Browse luxury apartments and villas for sale"},
                )
            ],
        )
        result = detector.detect(snapshot)

        assert result.detected_type == "real_estate"
        assert result.confidence > 0.5
        assert len(result.keyword_matches.get("real_estate", [])) > 0

    def test_detect_from_snapshot_ecommerce(self, sample_html_ecommerce):
        detector = BusinessDetector()
        snapshot = SnapshotData(
            url="https://example.com",
            pages=[
                PageSnapshot(
                    url="https://example.com",
                    title="ShopNow - Online Store",
                    headings={
                        "h1": ["Welcome to ShopNow"],
                        "h2": ["Featured Products"],
                        "h3": ["Product Name - $29.99"],
                    },
                    ctas=[
                        CTAInfo(text="Add to Cart", type="button"),
                        CTAInfo(text="Checkout", type="link"),
                    ],
                    navigation=NavigationInfo(
                        links=[
                            {"text": "Home", "href": "/"},
                            {"text": "Shop", "href": "/shop"},
                            {"text": "Cart", "href": "/cart"},
                        ]
                    ),
                    meta_tags={"description": "Shop the latest products online"},
                )
            ],
        )
        result = detector.detect(snapshot)

        assert result.detected_type == "ecommerce"
        assert result.confidence > 0.5

    def test_detect_from_snapshot_saas(self, sample_html_saas):
        detector = BusinessDetector()
        snapshot = SnapshotData(
            url="https://example.com",
            pages=[
                PageSnapshot(
                    url="https://example.com",
                    title="CloudApp - Project Management Software",
                    headings={
                        "h1": ["Manage Projects Like Never Before"],
                        "h2": ["Features"],
                        "h3": ["Business Plan - $49/month"],
                    },
                    ctas=[
                        CTAInfo(text="Start Free Trial", type="link"),
                        CTAInfo(text="Request Demo", type="link"),
                    ],
                    forms=[
                        FormInfo(has_email_field=True, field_count=2),
                    ],
                    navigation=NavigationInfo(
                        links=[
                            {"text": "Features", "href": "/features"},
                            {"text": "Pricing", "href": "/pricing"},
                            {"text": "Demo", "href": "/demo"},
                        ]
                    ),
                    meta_tags={"description": "The best project management platform"},
                )
            ],
        )
        result = detector.detect(snapshot)

        assert result.detected_type == "saas"
        assert result.confidence > 0.5


class TestKeywordMatches:
    def test_get_keyword_matches(self):
        detector = BusinessDetector()
        text = "property bedroom villa for sale apartment sqft"
        matches = detector._get_keyword_matches(text, BusinessType.REAL_ESTATE)

        assert "property" in matches
        assert "bedroom" in matches
        assert "villa" in matches
        assert len(matches) > 0


class TestIndustrySignals:
    def test_get_industry_signals_b2b(self):
        detector = BusinessDetector()
        text = "enterprise solutions for businesses and organizations"
        signals = detector._get_industry_signals(text)

        assert "b2b" in signals

    def test_get_industry_signals_local(self):
        detector = BusinessDetector()
        text = "visit our local store near me today"
        signals = detector._get_industry_signals(text)

        assert "local" in signals

    def test_get_industry_signals_premium(self):
        detector = BusinessDetector()
        text = "luxury exclusive high-end products"
        signals = detector._get_industry_signals(text)

        assert "premium" in signals


class TestFeatureIndicators:
    def test_detect_inquiry_form_feature(self):
        detector = BusinessDetector()
        snapshot = SnapshotData(
            url="https://example.com",
            pages=[
                PageSnapshot(
                    url="https://example.com",
                    forms=[
                        FormInfo(has_phone_field=True, has_email_field=True),
                    ],
                )
            ],
        )
        features = detector._detect_features(snapshot, BusinessType.REAL_ESTATE)

        assert "inquiry_form" in features

    def test_detect_signup_form_feature(self):
        detector = BusinessDetector()
        snapshot = SnapshotData(
            url="https://example.com",
            pages=[
                PageSnapshot(
                    url="https://example.com",
                    forms=[
                        FormInfo(has_email_field=True),
                    ],
                )
            ],
        )
        features = detector._detect_features(snapshot, BusinessType.SAAS)

        assert "signup_form" in features

    def test_detect_cart_button_feature(self):
        detector = BusinessDetector()
        snapshot = SnapshotData(
            url="https://example.com",
            pages=[
                PageSnapshot(
                    url="https://example.com",
                    ctas=[
                        CTAInfo(text="add to cart", type="button"),
                    ],
                )
            ],
        )
        features = detector._detect_features(snapshot, BusinessType.ECOMMERCE)

        assert "add_to_cart_button" in features
