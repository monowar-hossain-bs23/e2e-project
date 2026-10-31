"""Tests for PassportAdmin and VerificationInline configuration."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.passports.admin import PassportAdmin, VerificationInline
from apps.passports.models import Passport
from apps.verification.models import Verification

User = get_user_model()


@pytest.mark.django_db
class TestPassportAdmin:
    """Test suite for PassportAdmin readonly status and verification inline."""

    @pytest.fixture
    def admin_site(self) -> AdminSite:
        return AdminSite()

    @pytest.fixture
    def passport_admin(self, admin_site: AdminSite) -> PassportAdmin:
        return PassportAdmin(Passport, admin_site)

    @pytest.fixture
    def user(self) -> User:
        return User.objects.create_user(
            email="tenant_passport_admin@example.com",
            password="Password123!",
            display_name="AdminPassportTenant",
        )

    @pytest.fixture
    def passport(self, user: User) -> Passport:
        return Passport.objects.create(
            user=user,
            display_name="AdminPassportTenant",
        )

    def test_status_is_readonly(self, passport_admin: PassportAdmin) -> None:
        """Status must be read-only to prevent bypassing VerificationService (AD-10)."""
        assert "status" in passport_admin.readonly_fields

    def test_user_email_display(
        self, passport_admin: PassportAdmin, passport: Passport
    ) -> None:
        assert (
            passport_admin.user_email(passport) == "tenant_passport_admin@example.com"
        )

    def test_verification_inline_displays(
        self, passport: Passport, admin_site: AdminSite
    ) -> None:
        inline = VerificationInline(Passport, admin_site)
        assert not inline.has_add_permission(None)

        v = Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="nid_f.jpg",
            nid_back_path="nid_b.jpg",
            selfie_path="selfie.jpg",
            submitted_at=timezone.now(),
        )

        badge = inline.state_badge(v)
        assert "#0F6E7A" in badge
        assert "Submitted" in badge

        link = inline.review_link(v)
        assert f"/admin/verification/verification/{v.pk}/change/" in link
