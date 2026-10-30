"""Tests for VerificationAdmin and Django Admin review queue (FR-7, AD-10)."""

from datetime import timedelta

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.utils import timezone

from apps.passports.models import LifestyleProfile, Passport
from apps.verification.admin import VerificationAdmin
from apps.verification.models import Verification

User = get_user_model()


class MockRequest:
    """Mock request object for testing admin action callbacks."""

    def __init__(self, user: User) -> None:
        self.user = user
        rf = RequestFactory()
        req = rf.get("/admin/verification/verification/")
        req.session = "session"
        messages = FallbackStorage(req)
        req._messages = messages
        self._messages = messages


@pytest.mark.django_db
class TestVerificationAdmin:
    """Test suite for VerificationAdmin FIFO review queue and actions."""

    @pytest.fixture
    def admin_site(self) -> AdminSite:
        return AdminSite()

    @pytest.fixture
    def verification_admin(self, admin_site: AdminSite) -> VerificationAdmin:
        return VerificationAdmin(Verification, admin_site)

    @pytest.fixture
    def staff_user(self) -> User:
        return User.objects.create_user(
            email="staff_admin@example.com",
            password="Password123!",
            display_name="Staff Admin",
            is_staff=True,
        )

    @pytest.fixture
    def passport(self) -> Passport:
        user = User.objects.create_user(
            email="tenant_admin@example.com",
            password="Password123!",
            display_name="Tenant Admin",
        )
        passport = Passport.objects.create(
            user=user,
            display_name="AdminTestTenant",
        )
        LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.STUDENT,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Mirpur", "Uttara"],
            budget_min=6000,
            budget_max=12000,
        )
        return passport

    @pytest.fixture
    def verification(self, passport: Passport) -> Verification:
        return Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="verifications/test/nid_front.jpg",
            nid_back_path="verifications/test/nid_back.jpg",
            selfie_path="",
            submitted_at=timezone.now(),
        )

    def test_admin_fifo_ordering(self, verification_admin: VerificationAdmin) -> None:
        assert verification_admin.ordering == ["submitted_at"]

    def test_admin_display_methods(
        self,
        verification_admin: VerificationAdmin,
        verification: Verification,
        staff_user: User,
    ) -> None:
        assert verification_admin.id_short(verification) == str(verification.id)[:8]
        assert (
            verification_admin.passport_display_name(verification) == "AdminTestTenant"
        )

        badge_html = verification_admin.state_badge(verification)
        assert "#0F6E7A" in badge_html
        assert "Submitted" in badge_html

        assert verification_admin.reviewed_by_staff(verification) == "-"
        verification.reviewed_by = staff_user
        assert (
            verification_admin.reviewed_by_staff(verification)
            == "staff_admin@example.com"
        )

    def test_lifestyle_summary_display(
        self,
        verification_admin: VerificationAdmin,
        verification: Verification,
    ) -> None:
        summary = verification_admin.lifestyle_summary(verification)
        assert "Student" in summary
        assert "Mirpur, Uttara" in summary
        assert "৳6,000 – ৳12,000" in summary

    def test_document_previews(
        self,
        verification_admin: VerificationAdmin,
        verification: Verification,
    ) -> None:
        front_preview = verification_admin.nid_front_preview(verification)
        assert "/admin/verification/media/" in front_preview
        assert "nid_front" in front_preview

        # selfie_path is empty
        selfie_preview = verification_admin.selfie_preview(verification)
        assert "No document uploaded." in selfie_preview

    def test_approve_submissions_action(
        self,
        verification_admin: VerificationAdmin,
        verification: Verification,
        staff_user: User,
    ) -> None:
        rf = RequestFactory()
        request = rf.post("/admin/verification/verification/")
        request.user = staff_user
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        queryset = Verification.objects.filter(pk=verification.pk)
        verification_admin.approve_submissions(request, queryset)

        verification.refresh_from_db()
        assert verification.state == Verification.State.VERIFIED
        assert verification.passport.status == Passport.Status.VERIFIED

    def test_mark_in_review_action(
        self,
        verification_admin: VerificationAdmin,
        verification: Verification,
        staff_user: User,
    ) -> None:
        rf = RequestFactory()
        request = rf.post("/admin/verification/verification/")
        request.user = staff_user
        request.session = "session"
        messages = FallbackStorage(request)
        request._messages = messages

        queryset = Verification.objects.filter(pk=verification.pk)
        verification_admin.mark_in_review(request, queryset)

        verification.refresh_from_db()
        assert verification.state == Verification.State.REVIEWING
        assert verification.reviewed_by == staff_user

    def test_fifo_queue_ordering_in_queryset(self, passport: Passport) -> None:
        now = timezone.now()
        v1 = Verification.objects.create(
            passport=passport,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=now - timedelta(minutes=10),
        )
        v2 = Verification.objects.create(
            passport=passport,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=now - timedelta(minutes=30),
        )
        ordering_fields = Verification._meta.ordering
        ordered = list(Verification.objects.all().order_by(*ordering_fields))
        # v2 was submitted 30 mins ago, v1 10 mins ago -> v2 before v1 in FIFO
        first_indices = [v.id for v in ordered]
        assert first_indices.index(v2.id) < first_indices.index(v1.id)
