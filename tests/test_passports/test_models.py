"""Tests for Passport and LifestyleProfile domain models."""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.passports.models import LifestyleProfile, Passport

User = get_user_model()


@pytest.mark.django_db
class TestPassportModel:
    """Test suite for Passport aggregate root model."""

    def test_create_passport_default_state(self) -> None:
        user = User.objects.create_user(
            email="tenant1@example.com",
            password="Password123!",
            display_name="Tenant One",
        )
        passport = Passport.objects.create(
            user=user,
            display_name="TenantOne",
        )
        assert isinstance(passport.id, uuid.UUID)
        assert passport.user == user
        assert passport.display_name == "TenantOne"
        assert passport.status == Passport.Status.UNVERIFIED
        assert passport.is_verified is False
        assert str(passport) == "TenantOne (Unverified)"

    def test_passport_is_verified_property(self) -> None:
        user = User.objects.create_user(
            email="tenant2@example.com",
            password="Password123!",
            display_name="Tenant Two",
        )
        passport = Passport.objects.create(
            user=user,
            display_name="TenantTwo",
            status=Passport.Status.VERIFIED,
        )
        assert passport.is_verified is True
        assert str(passport) == "TenantTwo (Verified)"

    def test_passport_unique_display_name(self) -> None:
        user1 = User.objects.create_user(
            email="user1@example.com",
            password="Password123!",
            display_name="User One",
        )
        user2 = User.objects.create_user(
            email="user2@example.com",
            password="Password123!",
            display_name="User Two",
        )
        Passport.objects.create(user=user1, display_name="UniqueHandle")

        with pytest.raises(IntegrityError):
            Passport.objects.create(user=user2, display_name="UniqueHandle")

    def test_passport_clean_validation(self) -> None:
        user = User.objects.create_user(
            email="user3@example.com",
            password="Password123!",
            display_name="User Three",
        )
        passport = Passport(user=user, display_name="   ")
        with pytest.raises(ValidationError):
            passport.clean()

        valid_passport = Passport(user=user, display_name="  CleanName  ")
        valid_passport.clean()
        assert valid_passport.display_name == "CleanName"


@pytest.mark.django_db
class TestLifestyleProfileModel:
    """Test suite for LifestyleProfile entity and immutability invariants."""

    @pytest.fixture
    def passport(self) -> Passport:
        user = User.objects.create_user(
            email="tenant_lifestyle@example.com",
            password="Password123!",
            display_name="Tenant Lifestyle",
        )
        return Passport.objects.create(
            user=user,
            display_name="LifestyleUser",
            status=Passport.Status.UNVERIFIED,
        )

    def test_create_lifestyle_profile_success(self, passport: Passport) -> None:
        profile = LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.FEMALE,
            occupation=LifestyleProfile.Occupation.STUDENT,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Mirpur", "Dhanmondi"],
            budget_min=8000,
            budget_max=16000,
        )
        assert isinstance(profile.id, uuid.UUID)
        assert profile.passport == passport
        assert str(profile) == "Lifestyle for LifestyleUser"
        assert profile.area_preference == ["Mirpur", "Dhanmondi"]

    def test_lifestyle_profile_clean_validates_bounds(self, passport: Passport) -> None:
        profile = LifestyleProfile(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.PRIVATE_JOB,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.FLEXIBLE,
            area_preference=["Mirpur"],
            budget_min=20000,
            budget_max=10000,  # min > max
        )
        with pytest.raises(
            ValidationError,
            match="Minimum budget cannot be greater than maximum budget",
        ):
            profile.clean()

    def test_lifestyle_profile_clean_validates_areas(self, passport: Passport) -> None:
        profile = LifestyleProfile(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.PRIVATE_JOB,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.FLEXIBLE,
            area_preference=["InvalidArea"],
            budget_min=5000,
            budget_max=15000,
        )
        with pytest.raises(ValidationError, match="Invalid Dhaka area"):
            profile.clean()

    def test_immutability_invariant_post_verification(self, passport: Passport) -> None:
        """FR-3: Once passport is verified, profile changes are forbidden."""
        profile = LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.FREELANCER,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.NIGHT_OWL,
            area_preference=["Uttara"],
            budget_min=10000,
            budget_max=20000,
        )

        # Updating while unverified works without error
        profile.clean()
        profile.smoking = LifestyleProfile.Smoking.OCCASIONALLY
        profile.clean()
        profile.save()

        # Mark passport as VERIFIED
        passport.status = Passport.Status.VERIFIED
        passport.save()

        # Updating living search parameters (budget and area) on verified passport
        profile.budget_max = 25000
        profile.area_preference = ["Dhanmondi", "Mirpur"]
        profile.clean()
        profile.save()

        # Attempting to edit core lifestyle dimensions raises ValidationError
        profile.smoking = LifestyleProfile.Smoking.YES
        with pytest.raises(
            ValidationError,
            match="Core lifestyle dimensions are immutable once passport is verified",
        ):
            profile.clean()
