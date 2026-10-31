"""Tests for ListingService sole mutator and invariants (Story 018)."""

import io
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.models import AuditEntry
from apps.listings.constants import (
    ListingKind,
    PreferredGender,
    PreferredOccupation,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentUnit,
)
from apps.listings.models import Listing
from apps.listings.services.listing_service import ListingService
from apps.passports.models import Passport

VALID_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\xff\xc0\x00\x0b\x08\x00\x10\x00\x10\x01\x01\x11\x00"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)


def create_mock_photo(name: str = "room.jpg") -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name=name, content=VALID_JPEG_BYTES, content_type="image/jpeg"
    )


@pytest.mark.django_db
class TestListingService:
    """Test suite for ListingService creation, active cap, edits, and archival."""

    @pytest.fixture
    def verified_user(self) -> User:
        return User.objects.create_user(
            email="verified_host@example.com",
            password="Password123!",
            display_name="VerifiedHost",
        )

    @pytest.fixture
    def verified_passport(self, verified_user: User) -> Passport:
        return Passport.objects.create(
            user=verified_user,
            display_name="VerifiedHost",
            status=Passport.Status.VERIFIED,
        )

    @pytest.fixture
    def unverified_passport(self) -> Passport:
        user = User.objects.create_user(
            email="unverified_host@example.com",
            password="Password123!",
            display_name="UnverifiedHost",
        )
        return Passport.objects.create(
            user=user,
            display_name="UnverifiedHost",
            status=Passport.Status.UNVERIFIED,
        )

    def test_create_listing_success(self, verified_passport: Passport) -> None:
        photo = create_mock_photo()
        res = ListingService.create(
            author=verified_passport,
            kind=ListingKind.ROOM,
            rent_bdt=12000,
            rent_unit=RentUnit.PER_ROOM,
            area="Banani",
            body="Spacious room with attached bath.",
            pref_gender=PreferredGender.MALE,
            pref_smoking=PreferredSmoking.NO,
            pref_sleep=PreferredSleepSchedule.EARLY_BIRD,
            pref_occupation=[
                PreferredOccupation.STUDENT,
                PreferredOccupation.PRIVATE_JOB,
            ],
            photo_files=[photo],
        )

        assert res["ok"] is True
        listing = res["listing"]
        assert listing.author == verified_passport
        assert listing.kind == ListingKind.ROOM
        assert listing.photos.count() == 1
        assert listing.is_active is True

        # Verify audit log
        audit = AuditEntry.objects.filter(target_id=listing.id, action="create").first()
        assert audit is not None
        assert audit.actor_id == verified_passport.user.id

    def test_create_rejected_for_unverified_author(
        self, unverified_passport: Passport
    ) -> None:
        photo = create_mock_photo()
        res = ListingService.create(
            author=unverified_passport,
            kind=ListingKind.SEAT,
            rent_bdt=4000,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
            photo_files=[photo],
        )
        assert res["ok"] is False
        assert res["code"] == "unverified_author"

    def test_create_rejected_when_active_cap_reached(
        self, verified_passport: Passport
    ) -> None:
        # Create 3 active listings
        for _ in range(3):
            Listing.objects.create(
                author=verified_passport,
                kind=ListingKind.SEAT,
                rent_bdt=5000,
                rent_unit=RentUnit.PER_SEAT,
                area="Mirpur",
            )

        assert ListingService.check_active_cap(verified_passport) == 3

        photo = create_mock_photo()
        res = ListingService.create(
            author=verified_passport,
            kind=ListingKind.SEAT,
            rent_bdt=4500,
            rent_unit=RentUnit.PER_SEAT,
            area="Uttara",
            photo_files=[photo],
        )
        assert res["ok"] is False
        assert res["code"] == "active_cap_reached"

    def test_edit_locked_fields_rejected(self, verified_passport: Passport) -> None:
        listing = Listing.objects.create(
            author=verified_passport,
            kind=ListingKind.ROOM,
            rent_bdt=10000,
            rent_unit=RentUnit.PER_ROOM,
            area="Banani",
        )

        # Attempt to change area (locked)
        res = ListingService.edit(
            listing=listing,
            actor=verified_passport.user,
            fields={"area": "Dhanmondi"},
        )
        assert res["ok"] is False
        assert res["code"] == "field_locked"

        # Attempt to change kind (locked)
        res_kind = ListingService.edit(
            listing=listing,
            actor=verified_passport.user,
            fields={"kind": ListingKind.SEAT},
        )
        assert res_kind["ok"] is False
        assert res_kind["code"] == "field_locked"

    def test_edit_mutable_fields_success(self, verified_passport: Passport) -> None:
        photo = create_mock_photo()
        create_res = ListingService.create(
            author=verified_passport,
            kind=ListingKind.ROOM,
            rent_bdt=10000,
            rent_unit=RentUnit.PER_ROOM,
            area="Banani",
            body="Old note",
            photo_files=[photo],
        )
        assert create_res["ok"] is True
        listing = create_res["listing"]

        res = ListingService.edit(
            listing=listing,
            actor=verified_passport.user,
            fields={"rent_bdt": 11500, "body": "Updated note"},
        )
        assert res["ok"] is True
        listing.refresh_from_db()
        assert listing.rent_bdt == 11500
        assert listing.body == "Updated note"

    def test_withdraw_listing_success(self, verified_passport: Passport) -> None:
        listing = Listing.objects.create(
            author=verified_passport,
            kind=ListingKind.SEAT,
            rent_bdt=5000,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
        )
        assert listing.is_active is True

        res = ListingService.withdraw(listing, actor=verified_passport.user)
        assert res["ok"] is True
        listing.refresh_from_db()
        assert listing.is_withdrawn is True
        assert listing.is_active is False
        assert listing.status_label == "Withdrawn"

        # Active cap decremented
        assert ListingService.check_active_cap(verified_passport) == 0

    def test_archive_stale_listings_command(self, verified_passport: Passport) -> None:
        now = timezone.now()
        stale_time = now - timedelta(days=65)
        fresh_time = now - timedelta(days=20)

        # Stale listing
        l_stale = Listing.objects.create(
            author=verified_passport,
            kind=ListingKind.ROOM,
            rent_bdt=12000,
            rent_unit=RentUnit.PER_ROOM,
            area="Banani",
        )
        Listing.objects.filter(pk=l_stale.pk).update(created_at=stale_time)

        # Fresh listing
        l_fresh = Listing.objects.create(
            author=verified_passport,
            kind=ListingKind.SEAT,
            rent_bdt=5000,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
        )
        Listing.objects.filter(pk=l_fresh.pk).update(created_at=fresh_time)

        # Run command
        out = io.StringIO()
        call_command("archive_stale_listings", days=60, stdout=out)

        l_stale.refresh_from_db()
        l_fresh.refresh_from_db()
        assert l_stale.is_archived is True
        assert l_fresh.is_archived is False
        assert "Successfully archived 1 listing(s)" in out.getvalue()
