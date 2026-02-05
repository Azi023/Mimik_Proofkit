"""Conversion-focused rules for CTA, forms, and WhatsApp detection."""

from typing import List

from proofkit.schemas.finding import Finding, Severity, Category, Effort
from .base import BaseRule


class ConversionRules(BaseRule):
    """
    Rules focused on conversion optimization.

    Checks CTAs, forms, WhatsApp integration, and mobile conversion elements.
    """

    category = Category.CONVERSION

    def run(self) -> List[Finding]:
        """Execute all conversion rules."""
        self._check_cta_presence()
        self._check_cta_above_fold()
        self._check_whatsapp_presence()
        self._check_whatsapp_visibility()
        self._check_forms()
        self._check_mobile_ctas()
        self._check_contact_info()

        return self.findings

    def _check_cta_presence(self):
        """Check if CTAs are present on key pages."""
        homepage = self._get_homepage()

        if homepage:
            if not homepage.ctas:
                self.add_finding(
                    id="CONV-CTA-001",
                    severity=Severity.P0,
                    title="No CTAs detected on homepage",
                    summary="Homepage has no identifiable call-to-action buttons or links",
                    impact="Without CTAs, visitors have no clear next step. This is a complete conversion blocker.",
                    recommendation="Add prominent CTAs above the fold: 'Contact Us', 'Get Quote', 'Book Now', etc.",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(homepage.url, note="No CTAs found")],
                    tags=["cta", "critical"],
                )

        # Check all pages
        pages_without_ctas = []
        for page in self.raw_data.snapshot.pages:
            if not page.ctas:
                pages_without_ctas.append(page.url)

        if len(pages_without_ctas) > 1:
            self.add_finding(
                id="CONV-CTA-002",
                severity=Severity.P1,
                title=f"Multiple pages lack CTAs ({len(pages_without_ctas)} pages)",
                summary=f"{len(pages_without_ctas)} pages have no identifiable CTAs",
                impact="Pages without CTAs are dead ends for conversion",
                recommendation="Add relevant CTAs to all content pages",
                effort=Effort.M,
                evidence=[self.evidence_from_page(url) for url in pages_without_ctas[:3]],
                tags=["cta", "multiple-pages"],
            )

    def _check_cta_above_fold(self):
        """Check if CTAs are visible above the fold."""
        homepage = self._get_homepage()

        if homepage and homepage.ctas:
            above_fold_ctas = [c for c in homepage.ctas if c.is_above_fold]

            if not above_fold_ctas:
                self.add_finding(
                    id="CONV-FOLD-001",
                    severity=Severity.P1,
                    title="No CTA above the fold on homepage",
                    summary="All CTAs require scrolling to see",
                    impact="Users who don't scroll will miss all conversion opportunities. Many users never scroll.",
                    recommendation="Place primary CTA in hero section, visible without scrolling",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(homepage.url, note="CTAs below fold only")],
                    tags=["cta", "above-fold"],
                )

            visible_ctas = [c for c in homepage.ctas if c.is_visible]
            if len(visible_ctas) < len(homepage.ctas) * 0.5:
                self.add_finding(
                    id="CONV-VIS-001",
                    severity=Severity.P2,
                    title="Many CTAs are not visible",
                    summary=f"Only {len(visible_ctas)}/{len(homepage.ctas)} CTAs are visible",
                    impact="Hidden CTAs cannot drive conversions",
                    recommendation="Ensure CTAs are visible and not hidden by CSS or JavaScript",
                    effort=Effort.S,
                    tags=["cta", "visibility"],
                )

    def _check_whatsapp_presence(self):
        """Check for WhatsApp contact option."""
        has_whatsapp = False

        for page in self.raw_data.snapshot.pages:
            if page.whatsapp_links:
                has_whatsapp = True
                break

        if not has_whatsapp:
            # Only flag if likely relevant market (has phone numbers)
            has_phone = any(
                page.contact_info.get("phones") or page.contact_info.get("has_tel_link")
                for page in self.raw_data.snapshot.pages
            )

            if has_phone:
                self.add_finding(
                    id="CONV-WA-001",
                    severity=Severity.P2,
                    title="No WhatsApp contact option detected",
                    summary="Website has phone contact but no WhatsApp integration",
                    impact="WhatsApp is preferred contact method in many markets. Missing it loses potential leads.",
                    recommendation="Add WhatsApp button using wa.me/[number] link. Consider floating button for visibility.",
                    effort=Effort.S,
                    tags=["whatsapp", "contact"],
                    confidence=0.8,
                )

    def _check_whatsapp_visibility(self):
        """Check WhatsApp button visibility and placement."""
        for page in self.raw_data.snapshot.pages:
            if page.whatsapp_links:
                visible_wa = [w for w in page.whatsapp_links if w.get("is_visible")]
                above_fold_wa = [w for w in page.whatsapp_links if w.get("is_above_fold")]

                if page.whatsapp_links and not visible_wa:
                    self.add_finding(
                        id="CONV-WA-002",
                        severity=Severity.P1,
                        title="WhatsApp button not visible",
                        summary="WhatsApp link exists but is not visible on page",
                        impact="Hidden WhatsApp button defeats its purpose",
                        recommendation="Make WhatsApp button visible. Consider sticky/floating button.",
                        effort=Effort.S,
                        evidence=[self.evidence_from_page(page.url)],
                        tags=["whatsapp", "visibility"],
                    )

                if visible_wa and not above_fold_wa:
                    self.add_finding(
                        id="CONV-WA-003",
                        severity=Severity.P2,
                        title="WhatsApp button below fold",
                        summary="WhatsApp option requires scrolling to find",
                        impact="Users may not discover WhatsApp option before leaving",
                        recommendation="Add sticky WhatsApp button or place in header",
                        effort=Effort.S,
                        evidence=[self.evidence_from_page(page.url)],
                        tags=["whatsapp", "positioning"],
                    )
                break  # Only check first page with WhatsApp

    def _check_forms(self):
        """Check form quality and presence."""
        all_forms = []
        for page in self.raw_data.snapshot.pages:
            all_forms.extend(page.forms)

        if not all_forms:
            self.add_finding(
                id="CONV-FORM-001",
                severity=Severity.P1,
                title="No contact/inquiry forms detected",
                summary="No forms found across audited pages",
                impact="Forms are primary lead capture mechanism. Missing forms means missing leads.",
                recommendation="Add contact/inquiry form to key pages (homepage, contact, service pages)",
                effort=Effort.M,
                tags=["form", "lead-capture"],
            )
            return

        # Check form quality
        for page in self.raw_data.snapshot.pages:
            for form in page.forms:
                # Too many fields
                if form.field_count > 7:
                    self.add_finding(
                        id="CONV-FORM-002",
                        severity=Severity.P2,
                        title=f"Form has too many fields ({form.field_count})",
                        summary=f"Form on {self._page_name(page.url)} has {form.field_count} fields",
                        impact="Each additional field reduces conversion rate by ~10%. Long forms scare users away.",
                        recommendation="Reduce to essential fields only: Name, Email/Phone, Message. Collect more later.",
                        effort=Effort.S,
                        evidence=[self.evidence_from_page(page.url)],
                        tags=["form", "optimization"],
                    )

                # Missing key fields
                if not form.has_email_field and not form.has_phone_field:
                    self.add_finding(
                        id="CONV-FORM-003",
                        severity=Severity.P2,
                        title="Form missing contact field",
                        summary="Form has no email or phone field",
                        impact="Cannot follow up with leads if no contact method captured",
                        recommendation="Add email field (required) and phone field (optional)",
                        effort=Effort.S,
                        evidence=[self.evidence_from_page(page.url)],
                        tags=["form", "fields"],
                    )

                # Weak submit button text
                weak_texts = ["submit", "send", "go", "ok"]
                if form.submit_button_text.lower() in weak_texts:
                    self.add_finding(
                        id="CONV-FORM-004",
                        severity=Severity.P3,
                        title=f"Weak form button text: '{form.submit_button_text}'",
                        summary="Form submit button uses generic text",
                        impact="Action-oriented button text improves conversion rates",
                        recommendation="Use specific text: 'Get Quote', 'Book Now', 'Send Message'",
                        effort=Effort.S,
                        evidence=[self.evidence_from_page(page.url)],
                        tags=["form", "microcopy"],
                    )

    def _check_mobile_ctas(self):
        """Check CTA presence and visibility on mobile."""
        homepage = self._get_homepage()

        if homepage:
            desktop_ctas = len(homepage.ctas)
            mobile_ctas = len(homepage.mobile_ctas)

            if desktop_ctas > 0 and mobile_ctas == 0:
                self.add_finding(
                    id="CONV-MOB-001",
                    severity=Severity.P0,
                    title="No CTAs visible on mobile",
                    summary="Desktop has CTAs but none detected on mobile viewport",
                    impact="Mobile users (often 50%+ of traffic) have no conversion path",
                    recommendation="Ensure CTAs are visible on mobile. Check responsive design.",
                    effort=Effort.M,
                    evidence=[self.evidence_from_page(homepage.url)],
                    tags=["mobile", "cta", "critical"],
                )
            elif desktop_ctas > 0 and mobile_ctas < desktop_ctas * 0.5:
                self.add_finding(
                    id="CONV-MOB-002",
                    severity=Severity.P1,
                    title="Fewer CTAs visible on mobile",
                    summary=f"Mobile shows {mobile_ctas} CTAs vs {desktop_ctas} on desktop",
                    impact="Mobile users have fewer conversion opportunities",
                    recommendation="Review mobile design to ensure key CTAs remain visible",
                    effort=Effort.S,
                    evidence=[self.evidence_from_page(homepage.url)],
                    tags=["mobile", "cta"],
                )

    def _check_contact_info(self):
        """Check for contact information availability."""
        has_phone = False
        has_email = False

        for page in self.raw_data.snapshot.pages:
            if page.contact_info.get("phones"):
                has_phone = True
            if page.contact_info.get("emails"):
                has_email = True
            if page.contact_info.get("has_tel_link"):
                has_phone = True

        if not has_phone and not has_email:
            self.add_finding(
                id="CONV-CONTACT-001",
                severity=Severity.P1,
                title="No contact information detected",
                summary="No phone numbers or email addresses found",
                impact="Users cannot contact the business directly",
                recommendation="Add phone number and email in header/footer. Use clickable tel: and mailto: links.",
                effort=Effort.S,
                tags=["contact", "trust"],
            )
        elif has_phone:
            # Check if phone is clickable
            has_tel_link = any(
                page.contact_info.get("has_tel_link")
                for page in self.raw_data.snapshot.pages
            )
            if not has_tel_link:
                self.add_finding(
                    id="CONV-CONTACT-002",
                    severity=Severity.P2,
                    title="Phone number not clickable",
                    summary="Phone number displayed but not as tel: link",
                    impact="Mobile users cannot tap to call. Friction reduces calls.",
                    recommendation="Wrap phone numbers in <a href='tel:+1234567890'>",
                    effort=Effort.S,
                    tags=["contact", "mobile"],
                )
