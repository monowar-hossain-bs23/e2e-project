"""Tests for Listing and ListingPhoto domain models and validators (Story 017)."""

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.listings.constants import (
    ListingKind,
    PreferredGender,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentPeriod,
    RentUnit,
)
from apps.listings.models import Listing, ListingPhoto
from apps.passports.models import Passport


@pytest.mark.django_db
class TestListingModels:
    """Test suite for Listing aggregate root and constraints."""

    @pytest.fixture
    def author(self) -> Passport:
        user = User.objects.create_user(
            email="lister_model@example.com",
            password="Password123!",
            display_name="ListerModel",
        )
        return Passport.objects.create(
            user=user,
            display_name="ListerModel",
            status=Passport.Status.VERIFIED,
        )

    def test_listing_creation_defaults(self, author: Passport) -> None:
        listing = Listing.objects.create(
            author=author,
            kind=ListingKind.SEAT,
            rent_bdt=5000,
            rent_unit=RentUnit.PER_SEAT,
            area=["Mirpur", "Uttara"],
            body="Nice shared seat for student.",
        )
        assert listing.id is not None
        assert listing.rent_period == RentPeriod.PER_MONTH
        assert listing.pref_gender == PreferredGender.ANY
        assert listing.pref_smoking == PreferredSmoking.ANY
        assert listing.pref_sleep == PreferredSleepSchedule.FLEXIBLE
        assert listing.is_active is True
        assert listing.is_withdrawn is False
        assert listing.is_archived is False
        assert listing.status_label == "Active"
        assert "Seat in Mirpur, Uttara" in str(listing)

    def test_listing_clean_enforces_kind_and_rent_unit_parity(
        self, author: Passport
    ) -> None:
        listing = Listing(
            author=author,
            kind=ListingKind.SEAT,
            rent_bdt=5000,
            rent_unit=RentUnit.PER_ROOM,  # Mismatch!
            area=["Dhanmondi"],
        )
        with pytest.raises(ValidationError) as exc:
            listing.clean()
        assert "A seat listing must have rent unit set to 'per_seat'" in str(exc.value)

    def test_listing_clean_enforces_room_parity(self, author: Passport) -> None:
        listing = Listing(
            author=author,
            kind=ListingKind.ROOM,
            rent_bdt=12000,
            rent_unit=RentUnit.PER_SEAT,  # Mismatch!
            area=["Banani"],
        )
        with pytest.raises(ValidationError) as exc:
            listing.clean()
        assert "A room listing must have rent unit set to 'per_room'" in str(exc.value)

    def test_listing_invalid_rent_bounds(self, author: Passport) -> None:
        listing_low = Listing(
            author=author,
            kind=ListingKind.SEAT,
            rent_bdt=300,  # Below ৳500
            rent_unit=RentUnit.PER_SEAT,
            area=["Mirpur"],
        )
        with pytest.raises(ValidationError):
            listing_low.full_clean()

        listing_high = Listing(
            author=author,
            kind=ListingKind.ROOM,
            rent_bdt=60000,  # Above ৳50,000
            rent_unit=RentUnit.PER_ROOM,
            area=["Gulshan"],
        )
        with pytest.raises(ValidationError):
            listing_high.full_clean()

    def test_listing_invalid_area(self, author: Passport) -> None:
        listing = Listing(
            author=author,
            kind=ListingKind.ROOM,
            rent_bdt=15000,
            rent_unit=RentUnit.PER_ROOM,
            area=["NonExistentArea"],
        )
        with pytest.raises(ValidationError) as exc:
            listing.full_clean()
        assert "Invalid Dhaka area" in str(exc.value)

    def test_listing_photo_cascade_and_ordering(self, author: Passport) -> None:
        listing = Listing.objects.create(
            author=author,
            kind=ListingKind.ROOM,
            rent_bdt=15000,
            rent_unit=RentUnit.PER_ROOM,
            area=["Banani"],
        )
        p1 = ListingPhoto.objects.create(
            listing=listing, photo_path="listings/photos/p1.jpg", order=1
        )
        p0 = ListingPhoto.objects.create(
            listing=listing, photo_path="listings/photos/p0.jpg", order=0
        )

        assert listing.primary_photo == p0
        photos = list(listing.photos.all())
        assert photos[0] == p0
        assert photos[1] == p1

        listing_id = listing.id
        listing.delete()
        assert not ListingPhoto.objects.filter(listing_id=listing_id).exists()
