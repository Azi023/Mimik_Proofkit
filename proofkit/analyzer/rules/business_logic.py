"""Business logic rules for business-specific feature verification."""

from typing import List, Optional

from proofkit.schemas.finding import Finding, Severity, Category, Effort
from proofkit.schemas.business import BusinessType, BUSINESS_FEATURES, FeatureStatus
from .base import BaseRule


class BusinessLogicRules(BaseRule):
    """
    Rules for business-specific feature verification.

    Checks for expected features based on detected or specified business type.
    """

    category = Category.BUSINESS_LOGIC

    def run(self) -> List[Finding]:
        """Execute business logic rules."""
        if not self.business_type:
            # Try to use detected type
            detected = self.raw_data.business_signals.detected_type
            if detected:
                try:
                    self.business_type = BusinessType(detected)
                except ValueError:
                    return self.findings

        if not self.business_type:
            return self.findings

        expected = BUSINESS_FEATURES.get(self.business_type)
        if not expected:
            return self.findings

        self._check_must_have_features(expected.must_have)
        self._check_should_have_features(expected.should_have)

        return self.findings

    def _check_must_have_features(self, features: List[str]):
        """Check for critical business features."""
        for feature in features:
            status = self._detect_feature(feature)

            if status == FeatureStatus.MISSING:
                self.add_finding(
                    id=f"BIZ-MUST-{self._feature_id(feature)}",
                    severity=Severity.P0,
                    title=f"Critical feature missing: {self._feature_display_name(feature)}",
                    summary=f"As a {self.business_type.value} website, '{self._feature_display_name(feature)}' is expected but not detected",
                    impact=f"This feature is essential for {self.business_type.value} websites. Missing it may cause complete conversion failure.",
                    recommendation=self._get_feature_recommendation(feature),
                    effort=Effort.M,
                    tags=["business-critical", self.business_type.value],
                )
            elif status == FeatureStatus.BROKEN:
                self.add_finding(
                    id=f"BIZ-BROKEN-{self._feature_id(feature)}",
                    severity=Severity.P0,
                    title=f"Feature broken: {self._feature_display_name(feature)}",
                    summary=f"'{self._feature_display_name(feature)}' exists but doesn't appear to function correctly",
                    impact="Broken critical feature means users cannot complete their goal - 100% conversion loss on this path",
                    recommendation=f"Debug and fix {self._feature_display_name(feature)} functionality immediately",
                    effort=Effort.M,
                    tags=["broken", "critical"],
                )
            elif status == FeatureStatus.POORLY_PLACED:
                self.add_finding(
                    id=f"BIZ-PLACE-{self._feature_id(feature)}",
                    severity=Severity.P1,
                    title=f"Feature poorly positioned: {self._feature_display_name(feature)}",
                    summary=f"'{self._feature_display_name(feature)}' exists but is not easily discoverable",
                    impact="Users may not find this feature, reducing conversion rate",
                    recommendation=f"Move {self._feature_display_name(feature)} to more prominent position (above fold or sticky)",
                    effort=Effort.S,
                    tags=["positioning", "ux"],
                )

    def _check_should_have_features(self, features: List[str]):
        """Check for recommended business features."""
        for feature in features:
            status = self._detect_feature(feature)

            if status == FeatureStatus.MISSING:
                self.add_finding(
                    id=f"BIZ-SHOULD-{self._feature_id(feature)}",
                    severity=Severity.P2,
                    title=f"Recommended feature missing: {self._feature_display_name(feature)}",
                    summary=f"'{self._feature_display_name(feature)}' is common for {self.business_type.value} websites but not detected",
                    impact=f"Competitors likely have this feature. Missing it may put you at disadvantage.",
                    recommendation=self._get_feature_recommendation(feature),
                    effort=Effort.M,
                    confidence=0.7,
                    tags=["enhancement", self.business_type.value],
                )

    def _detect_feature(self, feature: str) -> FeatureStatus:
        """Detect if a feature exists and works."""
        detection_map = {
            "inquiry_form": self._detect_inquiry_form,
            "whatsapp_cta": self._detect_whatsapp,
            "property_listings": self._detect_listings,
            "product_catalog": self._detect_listings,
            "price_display": self._detect_prices,
            "image_gallery": self._detect_gallery,
            "location_map": self._detect_map,
            "virtual_tour": self._detect_virtual_tour,
            "add_to_cart": self._detect_cart,
            "checkout": self._detect_checkout,
            "search": self._detect_search,
            "booking_form": self._detect_booking,
            "reservation": self._detect_booking,
            "contact_form": self._detect_inquiry_form,
            "contact_info": self._detect_contact_info,
            "menu": self._detect_menu,
            "pricing_page": self._detect_pricing,
            "signup_form": self._detect_signup,
            "demo_request": self._detect_demo,
            "cta_button": self._detect_cta,
            "services_list": self._detect_services,
            "portfolio": self._detect_portfolio,
            "testimonials": self._detect_testimonials,
        }

        detector = detection_map.get(feature)
        if detector:
            return detector()

        # Default: assume found with low confidence
        return FeatureStatus.FOUND

    def _detect_inquiry_form(self) -> FeatureStatus:
        """Detect inquiry/contact form."""
        for page in self.raw_data.snapshot.pages:
            if page.forms:
                return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_whatsapp(self) -> FeatureStatus:
        """Detect WhatsApp contact option."""
        for page in self.raw_data.snapshot.pages:
            if page.whatsapp_links:
                visible = any(w.get("is_visible") for w in page.whatsapp_links)
                above_fold = any(w.get("is_above_fold") for w in page.whatsapp_links)
                if visible and above_fold:
                    return FeatureStatus.FOUND
                elif visible:
                    return FeatureStatus.POORLY_PLACED
                return FeatureStatus.POORLY_PLACED
        return FeatureStatus.MISSING

    def _detect_listings(self) -> FeatureStatus:
        """Detect property/product listings."""
        for page in self.raw_data.snapshot.pages:
            h2s = page.headings.get("h2", [])
            h3s = page.headings.get("h3", [])
            if len(h2s) >= 3 or len(h3s) >= 5:
                return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_prices(self) -> FeatureStatus:
        """Detect price displays."""
        # Check for price-related CTAs or headings
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                if "price" in cta.text.lower() or "$" in cta.text:
                    return FeatureStatus.FOUND
            for h in page.headings.get("h2", []) + page.headings.get("h3", []):
                if "$" in h or "price" in h.lower():
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_gallery(self) -> FeatureStatus:
        """Detect image gallery."""
        # Simplified - would need more sophisticated detection
        return FeatureStatus.FOUND

    def _detect_map(self) -> FeatureStatus:
        """Detect location map."""
        # Would check for Google Maps, Mapbox, etc.
        return FeatureStatus.FOUND

    def _detect_virtual_tour(self) -> FeatureStatus:
        """Detect virtual tour integration."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                if "tour" in cta.text.lower() or "virtual" in cta.text.lower():
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_cart(self) -> FeatureStatus:
        """Detect add to cart functionality."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                text = cta.text.lower()
                if "cart" in text or "add to" in text or "buy" in text:
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_checkout(self) -> FeatureStatus:
        """Detect checkout functionality."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                text = cta.text.lower()
                if "checkout" in text or "pay" in text or "purchase" in text:
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_search(self) -> FeatureStatus:
        """Detect search functionality."""
        # Would check for search input
        return FeatureStatus.FOUND

    def _detect_booking(self) -> FeatureStatus:
        """Detect booking/reservation form."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                text = cta.text.lower()
                if "book" in text or "reserve" in text or "schedule" in text:
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_contact_info(self) -> FeatureStatus:
        """Detect contact information."""
        for page in self.raw_data.snapshot.pages:
            if page.contact_info.get("phones") or page.contact_info.get("emails"):
                return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_menu(self) -> FeatureStatus:
        """Detect menu (restaurant)."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                if "menu" in cta.text.lower():
                    return FeatureStatus.FOUND
            if page.navigation:
                for link in page.navigation.links:
                    if "menu" in link.get("text", "").lower():
                        return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_pricing(self) -> FeatureStatus:
        """Detect pricing page."""
        for page in self.raw_data.snapshot.pages:
            if page.navigation:
                for link in page.navigation.links:
                    if "pricing" in link.get("text", "").lower():
                        return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_signup(self) -> FeatureStatus:
        """Detect signup form."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                text = cta.text.lower()
                if "sign up" in text or "register" in text or "get started" in text:
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_demo(self) -> FeatureStatus:
        """Detect demo request."""
        for page in self.raw_data.snapshot.pages:
            for cta in page.ctas:
                if "demo" in cta.text.lower():
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_cta(self) -> FeatureStatus:
        """Detect general CTA presence."""
        for page in self.raw_data.snapshot.pages:
            if page.ctas:
                return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_services(self) -> FeatureStatus:
        """Detect services listing."""
        for page in self.raw_data.snapshot.pages:
            if page.navigation:
                for link in page.navigation.links:
                    if "service" in link.get("text", "").lower():
                        return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_portfolio(self) -> FeatureStatus:
        """Detect portfolio section."""
        for page in self.raw_data.snapshot.pages:
            if page.navigation:
                for link in page.navigation.links:
                    text = link.get("text", "").lower()
                    if "portfolio" in text or "work" in text or "projects" in text:
                        return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _detect_testimonials(self) -> FeatureStatus:
        """Detect testimonials section."""
        for page in self.raw_data.snapshot.pages:
            for h in page.headings.get("h2", []):
                if "testimonial" in h.lower() or "review" in h.lower() or "client" in h.lower():
                    return FeatureStatus.FOUND
        return FeatureStatus.MISSING

    def _feature_id(self, feature: str) -> str:
        """Create short ID from feature name."""
        return feature[:10].upper().replace("_", "")

    def _feature_display_name(self, feature: str) -> str:
        """Convert feature key to display name."""
        return feature.replace("_", " ").title()

    def _get_feature_recommendation(self, feature: str) -> str:
        """Get recommendation for adding a feature."""
        recommendations = {
            "inquiry_form": "Add contact/inquiry form to key pages with minimal fields (Name, Email, Phone, Message)",
            "whatsapp_cta": "Add WhatsApp button in header and as floating sticky button. Use wa.me link.",
            "property_listings": "Create property listing grid with key details: image, title, price, location",
            "product_catalog": "Create product catalog with images, prices, and add-to-cart buttons",
            "price_display": "Display prices clearly. If pricing varies, show 'Starting from' or 'Contact for pricing'",
            "image_gallery": "Add image gallery with lightbox. Include multiple angles and details.",
            "location_map": "Embed Google Maps or Mapbox showing property/business location",
            "virtual_tour": "Consider adding Matterport or 360° virtual tour for immersive experience",
            "add_to_cart": "Implement add-to-cart functionality with clear feedback",
            "checkout": "Create streamlined checkout process with multiple payment options",
            "search": "Add search functionality to help users find content quickly",
            "booking_form": "Add booking/reservation form with date picker and availability check",
            "reservation": "Add reservation system with date/time selection",
            "contact_info": "Display phone number and email prominently in header/footer",
            "menu": "Create menu page with categories, items, descriptions, and prices",
            "pricing_page": "Create dedicated pricing page with clear plan comparison",
            "signup_form": "Add signup form with email field and clear value proposition",
            "demo_request": "Add 'Request Demo' CTA with booking integration",
            "cta_button": "Add prominent call-to-action buttons on key pages",
            "services_list": "Create services page listing all offerings with descriptions",
            "portfolio": "Add portfolio/work section showcasing past projects",
            "testimonials": "Add testimonials section with client quotes and photos",
        }
        return recommendations.get(feature, f"Implement {self._feature_display_name(feature)} functionality")
