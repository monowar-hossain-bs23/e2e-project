"""Unit tests for PassportSubmissionForm and validation rules (Story 015)."""

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.passports.forms import PassportSubmissionForm
from apps.passports.models import LifestyleProfile, Passport
from apps.passports.validators import MAX_BUDGET_BDT, MIN_BUDGET_BDT

User = get_user_model()


@pytest.mark.django_db
class TestPassportSubmissionForm:
    """Test suite for PassportSubmissionForm validation and file rules."""

    @pytest.fixture
    def user(self) -> User:
        return User.objects.create_user(
            email="form_user@example.com",
            password="Password123!",
            display_name="Form User",
        )

    @pytest.fixture
    def valid_files(
        self,
    ) -> dict[str, SimpleUploadedFile]:
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
    def valid_data(self) -> dict[str, str | list[str] | int]:
        return {
            "display_name": "TanvirAhmed",
            "gender": LifestyleProfile.Gender.MALE,
            "occupation": LifestyleProfile.Occupation.STUDENT,
            "smoking": LifestyleProfile.Smoking.NO,
            "sleep_schedule": LifestyleProfile.SleepSchedule.EARLY_BIRD,
            "area_preference": ["Mirpur", "Dhanmondi"],
            "budget_min": 6000,
            "budget_max": 14000,
        }

    def test_valid_form_submission(
        self,
        user: User,
        valid_data: dict[str, str | list[str] | int],
        valid_files: dict[str, SimpleUploadedFile],
    ) -> None:
        form = PassportSubmissionForm(data=valid_data, files=valid_files, user=user)
        assert form.is_valid(), form.errors
        assert form.cleaned_data["display_name"] == "TanvirAhmed"
        assert form.cleaned_data["budget_min"] == 6000

    def test_display_name_taken_by_other_user(
        self,
        user: User,
        valid_data: dict[str, str | list[str] | int],
        valid_files: dict[str, SimpleUploadedFile],
    ) -> None:
        other_user = User.objects.create_user(
            email="other_tenant@example.com",
            password="Password123!",
            display_name="Other Tenant",
        )
        Passport.objects.create(user=other_user, display_name="TanvirAhmed")

        form = PassportSubmissionForm(data=valid_data, files=valid_files, user=user)
        assert not form.is_valid()
        assert "display_name" in form.errors
        assert "already registered by another tenant" in form.errors["display_name"][0]

    def test_display_name_matching_current_user_allowed(
        self,
        user: User,
        valid_data: dict[str, str | list[str] | int],
        valid_files: dict[str, SimpleUploadedFile],
    ) -> None:
        Passport.objects.create(user=user, display_name="TanvirAhmed")

        form = PassportSubmissionForm(data=valid_data, files=valid_files, user=user)
        assert form.is_valid(), form.errors

    def test_display_name_invalid_format(
        self,
        user: User,
        valid_data: dict[str, str | list[str] | int],
        valid_files: dict[str, SimpleUploadedFile],
    ) -> None:
        valid_data["display_name"] = "Invalid<script>"
        form = PassportSubmissionForm(data=valid_data, files=valid_files, user=user)
        assert not form.is_valid()
        assert "display_name" in form.errors

    def test_budget_range_ordering_error(
        self,
        user: User,
        valid_data: dict[str, str | list[str] | int],
        valid_files: dict[str, SimpleUploadedFile],
    ) -> None:
        valid_data["budget_min"] = 18000
        valid_data["budget_max"] = 8000  # min > max
        form = PassportSubmissionForm(data=valid_data, files=valid_files, user=user)
        assert not form.is_valid()
        assert "budget_min" in form.errors

    def test_budget_bounds_error(
        self,
        user: User,
        valid_data: dict[str, str | list[str] | int],
        valid_files: dict[str, SimpleUploadedFile],
    ) -> None:
        valid_data["budget_min"] = MIN_BUDGET_BDT - 100
        valid_data["budget_max"] = MAX_BUDGET_BDT + 5000
        form = PassportSubmissionForm(data=valid_data, files=valid_files, user=user)
        assert not form.is_valid()
        assert "budget_min" in form.errors
        assert "budget_max" in form.errors

    def test_empty_dhaka_areas_error(
        self,
        user: User,
        valid_data: dict[str, str | list[str] | int],
        valid_files: dict[str, SimpleUploadedFile],
    ) -> None:
        valid_data["area_preference"] = []
        form = PassportSubmissionForm(data=valid_data, files=valid_files, user=user)
        assert not form.is_valid()
        assert "area_preference" in form.errors

    def test_file_upload_oversized_rejected(
        self,
        user: User,
        valid_data: dict[str, str | list[str] | int],
        valid_files: dict[str, SimpleUploadedFile],
    ) -> None:
        oversized = SimpleUploadedFile(
            "large.jpg",
            b"x" * (6 * 1024 * 1024),
            content_type="image/jpeg",
        )
        valid_files["nid_front"] = oversized
        form = PassportSubmissionForm(data=valid_data, files=valid_files, user=user)
        assert not form.is_valid()
        assert "nid_front" in form.errors
        assert "exceeds maximum permitted limit" in form.errors["nid_front"][0]

    def test_file_upload_forbidden_extension_rejected(
        self,
        user: User,
        valid_data: dict[str, str | list[str] | int],
        valid_files: dict[str, SimpleUploadedFile],
    ) -> None:
        bad_doc = SimpleUploadedFile(
            "doc.pdf", b"pdf-content", content_type="application/pdf"
        )
        valid_files["selfie"] = bad_doc
        form = PassportSubmissionForm(data=valid_data, files=valid_files, user=user)
        assert not form.is_valid()
        assert "selfie" in form.errors

    def test_locale_form_mixin_attributes(self, user: User) -> None:
        form = PassportSubmissionForm(user=user)
        widget = form.fields["display_name"].widget
        assert "font-bengali-ready" in widget.attrs.get("class", "")
        assert widget.attrs.get("lang") == "auto"
