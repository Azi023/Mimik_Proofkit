"""Business type and feature check models."""

from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum


class BusinessType(str, Enum):
    """Supported business types for context-aware auditing."""
    REAL_ESTATE = "real_estate"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    HOSPITALITY = "hospitality"
    RESTAURANT = "restaurant"
    HEALTHCARE = "healthcare"
    AGENCY = "agency"
    OTHER = "other"


class FeatureStatus(str, Enum):
    """Status of an expected feature."""
    FOUND = "found"
    MISSING = "missing"
    BROKEN = "broken"
    POORLY_PLACED = "poorly_placed"


class FeatureCheck(BaseModel):
    """Result of checking for an expected feature."""
    feature_name: str
    expected: bool
    found: bool
    functional: Optional[bool] = None
    status: FeatureStatus
    location: Optional[str] = None  # "homepage", "header", "footer", etc.
    accessibility: Optional[str] = None  # "above_fold", "below_fold", "buried"
    selector: Optional[str] = None
    screenshot_path: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"use_enum_values": True}


class ExpectedFeatures(BaseModel):
    """Expected features for a business type."""
    business_type: BusinessType
    must_have: List[str]
    should_have: List[str]
    nice_to_have: List[str]

    model_config = {"use_enum_values": True}


# Feature expectations by business type
BUSINESS_FEATURES: Dict[BusinessType, ExpectedFeatures] = {
    BusinessType.REAL_ESTATE: ExpectedFeatures(
        business_type=BusinessType.REAL_ESTATE,
        must_have=["property_listings", "inquiry_form", "location_map", "price_display", "image_gallery"],
        should_have=["whatsapp_cta", "virtual_tour", "floor_plans", "payment_calculator"],
        nice_to_have=["compare_units", "favorites", "agent_profiles", "mortgage_calculator"],
    ),
    BusinessType.ECOMMERCE: ExpectedFeatures(
        business_type=BusinessType.ECOMMERCE,
        must_have=["product_catalog", "add_to_cart", "checkout", "search", "price_display"],
        should_have=["filters", "reviews", "wishlist", "stock_status"],
        nice_to_have=["related_products", "recently_viewed", "size_guide", "compare"],
    ),
    BusinessType.SAAS: ExpectedFeatures(
        business_type=BusinessType.SAAS,
        must_have=["pricing_page", "signup_form", "feature_list", "cta_button"],
        should_have=["demo_request", "testimonials", "integrations", "faq"],
        nice_to_have=["comparison_table", "case_studies", "api_docs", "status_page"],
    ),
    BusinessType.HOSPITALITY: ExpectedFeatures(
        business_type=BusinessType.HOSPITALITY,
        must_have=["room_listings", "booking_form", "image_gallery", "price_display", "location_map"],
        should_have=["amenities", "reviews", "whatsapp_cta", "availability_calendar"],
        nice_to_have=["virtual_tour", "packages", "local_attractions", "loyalty_program"],
    ),
    BusinessType.RESTAURANT: ExpectedFeatures(
        business_type=BusinessType.RESTAURANT,
        must_have=["menu", "location_map", "contact_info", "hours"],
        should_have=["online_ordering", "reservation", "whatsapp_cta", "image_gallery"],
        nice_to_have=["reviews", "delivery_tracking", "loyalty_program", "special_offers"],
    ),
    BusinessType.HEALTHCARE: ExpectedFeatures(
        business_type=BusinessType.HEALTHCARE,
        must_have=["services_list", "contact_info", "location_map", "appointment_booking"],
        should_have=["doctor_profiles", "insurance_info", "whatsapp_cta", "patient_portal"],
        nice_to_have=["telehealth", "reviews", "health_resources", "faq"],
    ),
    BusinessType.AGENCY: ExpectedFeatures(
        business_type=BusinessType.AGENCY,
        must_have=["services_list", "portfolio", "contact_form", "about_page"],
        should_have=["case_studies", "team_page", "testimonials", "whatsapp_cta"],
        nice_to_have=["blog", "pricing", "client_logos", "awards"],
    ),
    BusinessType.OTHER: ExpectedFeatures(
        business_type=BusinessType.OTHER,
        must_have=["contact_info", "about_page", "cta_button"],
        should_have=["services_list", "whatsapp_cta", "location_map"],
        nice_to_have=["testimonials", "faq", "blog"],
    ),
}
