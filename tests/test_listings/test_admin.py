"""Tests for ListingAdmin and ListingPhotoAdmin (Story 018)."""

import pytest
from django.contrib.admin.sites import AdminSite

from apps.accounts.models import User
from apps.listings.admin import ListingAdmin, ListingPhotoInline
from apps.listings.constants import ListingKind, RentUnit
from apps.listings.models import Listing, ListingPhoto
from apps.passports.models import Passport


@pytest.mark.django_db
class TestListingAdmin:
    """Test suite for ListingAdmin display methods and inlines."""

    @pytest.fixture
    def admin_site(self) -> AdminSite:
        return AdminSite()

    @pytest.fixture
    def listing_admin(self, admin_site: AdminSite) -> ListingAdmin:
        return ListingAdmin(Listing, admin_site)

    @pytest.fixture
    def passport(self) -> Passport:
        user = User.objects.create_user(
            email="admin_lister@example.com",
            password="Password123!",
            display_name="AdminLister",
        )
        return Passport.objects.create(
            user=user,
            display_name="AdminLister",
            status=Passport.Status.VERIFIED,
        )

    def test_admin_display_methods(
        self, listing_admin: ListingAdmin, passport: Passport
    ) -> None:
        listing = Listing.objects.create(
            author=passport,
            kind=ListingKind.ROOM,
            rent_bdt=14000,
            rent_unit=RentUnit.PER_ROOM,
            area="Banani",
        )

        assert listing_admin.id_short(listing) == str(listing.id)[:8]
        assert listing_admin.author_display_name(listing) == "AdminLister"
        assert "Room" in listing_admin.kind_badge(listing)
        assert "৳14,000/Per Room" in listing_admin.rent_display(listing)
        assert listing_admin.areas_display(listing) == "Banani"
        assert "Active" in listing_admin.status_badge(listing)

    def test_photo_inline_thumbnail(
        self, admin_site: AdminSite, passport: Passport
    ) -> None:
        listing = Listing.objects.create(
            author=passport,
            kind=ListingKind.SEAT,
            rent_bdt=6000,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
        )
        photo = ListingPhoto.objects.create(
            listing=listing,
            photo_path="listings/photos/test.jpg",
            order=0,
        )
        inline = ListingPhotoInline(Listing, admin_site)
        html = inline.photo_thumbnail(photo)
        assert "/media/listings/photos/test.jpg" in html
