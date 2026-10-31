"""Integration tests for Passport wizard, guards, and dashboard views."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.passports.models import LifestyleProfile, Passport
from apps.verification.models import Verification
from apps.verification.services.reject_reasons import RejectReason

User = get_user_model()


@pytest.mark.django_db
class TestPassportWizardView:
    """Test suite for PassportWizardView access control, guards, and submissions."""

    @pytest.fixture
    def client(self) -> Client:
        return Client()

    @pytest.fixture
    def user(self) -> User:
        return User.objects.create_user(
            email="wizard_tenant@example.com",
            password="Password123!",
            display_name="Wizard Tenant",
        )

    @pytest.fixture
    def sample_files(self) -> dict[str, SimpleUploadedFile]:
        return {
            "nid_front": SimpleUploadedFile(
                "front.jpg", b"fake-front", content_type="image/jpeg"
            ),
            "nid_back": SimpleUploadedFile(
                "back.jpg", b"fake-back", content_type="image/jpeg"
            ),
            "selfie": SimpleUploadedFile(
                "selfie.png", b"fake-selfie", content_type="image/png"
            ),
        }

    @pytest.fixture
    def valid_post_data(self) -> dict[str, str | list[str] | int]:
        return {
            "display_name": "WizardUser",
            "gender": LifestyleProfile.Gender.FEMALE,
            "occupation": LifestyleProfile.Occupation.STUDENT,
            "smoking": LifestyleProfile.Smoking.NO,
            "sleep_schedule": LifestyleProfile.SleepSchedule.EARLY_BIRD,
            "area_preference": ["Mirpur", "Uttara"],
            "budget_min": 7000,
            "budget_max": 15000,
        }

    def test_anonymous_access_redirected(self, client: Client) -> None:
        url = reverse("passport_create")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_authenticated_user_loads_wizard(self, client: Client, user: User) -> None:
        client.force_login(user)
        url = reverse("passport_create")
        response = client.get(url)
        assert response.status_code == 200
        assert "Create Your Tenant Passport" in response.content.decode()

    def test_guard_verified_user_redirected_to_dashboard(
        self, client: Client, user: User
    ) -> None:
        client.force_login(user)
        Passport.objects.create(
            user=user,
            display_name="AlreadyVerified",
            status=Passport.Status.VERIFIED,
        )

        response = client.get(reverse("passport_create"))
        assert response.status_code == 302
        assert response.url == reverse("dashboard")

    def test_guard_pending_user_redirected_to_dashboard(
        self, client: Client, user: User
    ) -> None:
        client.force_login(user)
        Passport.objects.create(
            user=user,
            display_name="AlreadyPending",
            status=Passport.Status.PENDING,
        )

        response = client.get(reverse("passport_create"))
        assert response.status_code == 302
        assert response.url == reverse("dashboard")

    def test_guard_active_cooldown_redirected_to_dashboard(
        self, client: Client, user: User
    ) -> None:
        client.force_login(user)
        passport = Passport.objects.create(
            user=user,
            display_name="RejectedTenant",
            status=Passport.Status.REJECTED,
        )
        Verification.objects.create(
            passport=passport,
            state=Verification.State.REJECTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            reject_reason=RejectReason.ILLEGIBLE,
            submitted_at=timezone.now() - timedelta(hours=2),
            last_rejection_at=timezone.now() - timedelta(hours=2),
        )

        response = client.get(reverse("passport_create"))
        assert response.status_code == 302
        assert response.url == reverse("dashboard")

    def test_get_wizard_prepopulates_existing_draft(
        self, client: Client, user: User
    ) -> None:
        client.force_login(user)
        passport = Passport.objects.create(
            user=user,
            display_name="PrefillHandle",
            status=Passport.Status.UNVERIFIED,
        )
        LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.GARMENTS_WORKER,
            smoking=LifestyleProfile.Smoking.OCCASIONALLY,
            sleep_schedule=LifestyleProfile.SleepSchedule.FLEXIBLE,
            area_preference=["Mirpur"],
            budget_min=5000,
            budget_max=10000,
        )

        response = client.get(reverse("passport_create"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "PrefillHandle" in content
        assert "garments_worker" in content

    def test_post_invalid_data_rerenders_with_errors(
        self, client: Client, user: User
    ) -> None:
        client.force_login(user)
        response = client.post(
            reverse("passport_create"),
            data={"display_name": ""},
        )
        assert response.status_code == 200
        assert "This field is required." in response.content.decode()

    def test_post_valid_data_creates_models_and_redirects(
        self,
        client: Client,
        user: User,
        valid_post_data: dict[str, str | list[str] | int],
        sample_files: dict[str, SimpleUploadedFile],
    ) -> None:
        client.force_login(user)
        data = {**valid_post_data, **sample_files}
        response = client.post(reverse("passport_create"), data=data)

        assert response.status_code == 302
        assert response.url == reverse("dashboard")

        passport = Passport.objects.get(user=user)
        assert passport.display_name == "WizardUser"
        assert passport.status == Passport.Status.PENDING

        profile = passport.lifestyle_profile
        assert profile.gender == LifestyleProfile.Gender.FEMALE
        assert profile.area_preference == ["Mirpur", "Uttara"]

        verification = Verification.objects.get(passport=passport)
        assert verification.state == Verification.State.SUBMITTED
        assert verification.nid_front_path.startswith("verifications/")


@pytest.mark.django_db
class TestDashboardView:
    """Test suite for DashboardView lifecycle state routing (Story 016)."""

    @pytest.fixture
    def client(self) -> Client:
        return Client()

    @pytest.fixture
    def tenant(self) -> User:
        return User.objects.create_user(
            email="dashboard_tenant@example.com",
            password="Password123!",
            display_name="Dash Tenant",
        )

    def test_anonymous_user_redirected_to_login(self, client: Client) -> None:
        response = client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_unverified_user_renders_teaser_screen(
        self, client: Client, tenant: User
    ) -> None:
        client.force_login(tenant)
        response = client.get(reverse("dashboard"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Unlock Verified Dhaka Listings" in content
        assert "Verify Passport Now" in content
        assert "Private PII storage" in content

    def test_pending_user_renders_in_review_screen(
        self, client: Client, tenant: User
    ) -> None:
        client.force_login(tenant)
        passport = Passport.objects.create(
            user=tenant,
            display_name="PendingTenant",
            status=Passport.Status.PENDING,
        )
        Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=timezone.now(),
        )

        response = client.get(reverse("dashboard"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Documents Under Review" in content
        assert "Review SLA:" in content
        assert "24 hours" in content

    def test_rejected_user_renders_rejection_screen_with_cooldown(
        self, client: Client, tenant: User
    ) -> None:
        client.force_login(tenant)
        passport = Passport.objects.create(
            user=tenant,
            display_name="RejectedTenant",
            status=Passport.Status.REJECTED,
        )
        recent_time = timezone.now() - timedelta(hours=4)
        Verification.objects.create(
            passport=passport,
            state=Verification.State.REJECTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            reject_reason=RejectReason.ILLEGIBLE,
            reviewer_notes="NID card was blurry.",
            submitted_at=recent_time - timedelta(hours=1),
            last_rejection_at=recent_time,
        )

        response = client.get(reverse("dashboard"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Verification could not be approved" in content
        assert "Illegible Image" in content
        assert "NID card was blurry." in content
        assert 'id="cooldown-timer"' in content
        assert "disabled" in content

    def test_rejected_user_with_expired_cooldown_renders_enabled_button(
        self, client: Client, tenant: User
    ) -> None:
        client.force_login(tenant)
        passport = Passport.objects.create(
            user=tenant,
            display_name="ExpiredCooldownTenant",
            status=Passport.Status.REJECTED,
        )
        past_time = timezone.now() - timedelta(hours=26)
        Verification.objects.create(
            passport=passport,
            state=Verification.State.REJECTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            reject_reason=RejectReason.TAMPERING_SUSPECTED,
            submitted_at=past_time - timedelta(hours=1),
            last_rejection_at=past_time,
        )

        response = client.get(reverse("dashboard"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "You can now submit new documents" in content
        assert "Resubmit Documents" in content

    def test_verified_user_renders_badge_and_profile(
        self, client: Client, tenant: User
    ) -> None:
        client.force_login(tenant)
        passport = Passport.objects.create(
            user=tenant,
            display_name="VerifiedTenant",
            status=Passport.Status.VERIFIED,
        )
        LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.PRIVATE_JOB,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Gulshan", "Banani"],
            budget_min=12000,
            budget_max=25000,
        )

        response = client.get(reverse("dashboard"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Verified Tenant Active" in content
        assert "Verified Tenant" in content
        assert "Gulshan" in content
        assert "৳12000" in content

    def test_htmx_status_partial_view(self, client: Client, tenant: User) -> None:
        client.force_login(tenant)
        response = client.get(
            reverse("dashboard_status_partial"),
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert 'id="status-container"' in response.content.decode()
