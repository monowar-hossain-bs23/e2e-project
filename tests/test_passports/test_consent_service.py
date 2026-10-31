"""Tests for ConsentService and ListingProjection (Story 024, AD-3)."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.listings.constants import (
    ListingKind,
    PreferredGender,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentUnit,
)
from apps.listings.models import Listing, ListingPhoto
from apps.passports.models import LifestyleProfile, Passport
from apps.passports.services.consent_service import ConsentService
from apps.verification.models import Verification


@pytest.mark.django_db
class TestConsentService:
    """Test suite for ConsentService projection and PII redaction."""

    @pytest.fixture
    def lister_user(self) -> User:
        user = User.objects.create_user(
            email="tanvir@example.com",
            password="Password123!",
            display_name="Tanvir H.",
            phone_number="+8801712345678",
        )
        return user

    @pytest.fixture
    def lister_passport(self, lister_user: User) -> Passport:
        passport = Passport.objects.create(
            user=lister_user,
            display_name="Tanvir H.",
            status=Passport.Status.VERIFIED,
        )
        LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.STUDENT,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Mirpur", "Dhanmondi"],
            budget_min=3000,
            budget_max=6000,
        )
        return passport

    @pytest.fixture
    def sample_listing(self, lister_passport: Passport) -> Listing:
        listing = Listing.objects.create(
            author=lister_passport,
            kind=ListingKind.SEAT,
            rent_bdt=4500,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
            body="Quiet mess, 2-min walk to campus.",
            pref_gender=PreferredGender.MALE,
            pref_smoking=PreferredSmoking.NO,
            pref_sleep=PreferredSleepSchedule.EARLY_BIRD,
            pref_occupation=["student"],
        )
        ListingPhoto.objects.create(
            listing=listing,
            photo_path="listings/photos/test1.jpg",
            order=0,
        )
        return listing

    @pytest.fixture
    def verified_seeker(self) -> User:
        user = User.objects.create_user(
            email="seeker_verified@example.com",
            password="Password123!",
            display_name="Seeker Verified",
            phone_number="+8801999999999",
        )
        passport = Passport.objects.create(
            user=user,
            display_name="Seeker Verified",
            status=Passport.Status.VERIFIED,
        )
        LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.STUDENT,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Mirpur"],
            budget_min=3000,
            budget_max=5000,
        )
        return user

    @pytest.fixture
    def unverified_seeker(self) -> User:
        user = User.objects.create_user(
            email="seeker_unverified@example.com",
            password="Password123!",
            display_name="Seeker Unverified",
        )
        Passport.objects.create(
            user=user,
            display_name="Seeker Unverified",
            status=Passport.Status.UNVERIFIED,
        )
        return user

    def test_anonymous_viewer_redacts_contact_info(
        self, sample_listing: Listing
    ) -> None:
        """Anonymous visitors receive None for phone and email with locked panel."""
        proj = ConsentService.render_listing(viewer=None, listing=sample_listing)

        assert proj.id == sample_listing.id
        assert proj.kind_display == "Seat"
        assert proj.area == "Mirpur"
        assert proj.rent_bdt == 4500
        assert proj.is_contact_locked is True
        assert proj.lister_email is None
        assert proj.lister_phone is None
        assert proj.author_lifestyle_summary == "Verify to see lifestyle fit"
        assert proj.author_lifestyle_chips == ()

    def test_unverified_viewer_redacts_contact_info(
        self, unverified_seeker: User, sample_listing: Listing
    ) -> None:
        """Unverified logged-in users receive None for phone/email with locked panel."""
        proj = ConsentService.render_listing(
            viewer=unverified_seeker, listing=sample_listing
        )

        assert proj.is_contact_locked is True
        assert proj.lister_email is None
        assert proj.lister_phone is None
        assert proj.author_lifestyle_summary == "Verify to see lifestyle fit"

    def test_verified_viewer_reveals_contact_info(
        self, verified_seeker: User, sample_listing: Listing
    ) -> None:
        """Verified seekers receive unredacted email and phone."""
        proj = ConsentService.render_listing(
            viewer=verified_seeker,
            listing=sample_listing,
            compatibility_hint=5,
        )

        assert proj.is_contact_locked is False
        assert proj.lister_email == "tanvir@example.com"
        assert proj.lister_phone == "+8801712345678"
        assert proj.author_display_name == "Tanvir H."
        assert proj.compatibility_hint == 5
        assert "Non-smoker" in proj.author_lifestyle_summary
        assert "Early bird" in proj.author_lifestyle_chips

    def test_author_always_views_own_contact_details(
        self, lister_user: User, sample_listing: Listing
    ) -> None:
        """Author viewing their own listing always sees their contact info."""
        proj = ConsentService.render_listing(viewer=lister_user, listing=sample_listing)

        assert proj.is_contact_locked is False
        assert proj.lister_email == "tanvir@example.com"
        assert proj.lister_phone == "+8801712345678"

    def test_author_tenure_display_calculation(
        self, lister_passport: Passport, sample_listing: Listing
    ) -> None:
        """Tenure formats days, months, or years accurately."""
        now = timezone.now()
        # Set verification date 95 days ago (~3 months)
        v_date = now - timedelta(days=95)
        Verification.objects.create(
            passport=lister_passport,
            state=Verification.State.VERIFIED,
            nid_front_path="nid_f.jpg",
            nid_back_path="nid_b.jpg",
            selfie_path="selfie.jpg",
            submitted_at=v_date,
            reviewed_at=v_date,
        )

        tenure = ConsentService.compute_author_tenure(lister_passport)
        assert "3 months" in tenure
