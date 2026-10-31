"""Integration tests for listing views, gatekeeper mixin, cap, and lifecycle."""

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

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

User = get_user_model()

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


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def verified_user() -> User:
    user = User.objects.create_user(
        email="lister_verified@example.com",
        password="Password123!",
        display_name="VerifiedLister",
    )
    Passport.objects.create(
        user=user,
        display_name="VerifiedLister",
        status=Passport.Status.VERIFIED,
    )
    return user


@pytest.fixture
def other_verified_user() -> User:
    user = User.objects.create_user(
        email="other_verified@example.com",
        password="Password123!",
        display_name="OtherLister",
    )
    Passport.objects.create(
        user=user,
        display_name="OtherLister",
        status=Passport.Status.VERIFIED,
    )
    return user


@pytest.mark.django_db
class TestVerifiedTenantRequiredMixin:
    """Test suite for VerifiedTenantRequiredMixin access gating (Story 020)."""

    def test_anonymous_user_redirected_to_login(self, client: Client) -> None:
        url = reverse("listing_create")
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("login") in response.url
        assert "next=" in response.url

    def test_authenticated_no_passport_redirects_to_passport_create(
        self, client: Client
    ) -> None:
        user = User.objects.create_user(
            email="nopassport@example.com",
            password="Password123!",
            display_name="NoPassport",
        )
        client.force_login(user)
        response = client.get(reverse("listing_create"), follow=True)
        assert response.status_code == 200
        # Redirected to passport wizard step 1
        assert response.redirect_chain[0][0] == reverse("passport_create")
        messages = list(response.context["messages"])
        assert any(
            "Please complete your Tenant Passport" in m.message for m in messages
        )

    def test_authenticated_unverified_passport_redirects_to_passport_create(
        self, client: Client
    ) -> None:
        user = User.objects.create_user(
            email="unverified@example.com",
            password="Password123!",
            display_name="Unverified",
        )
        Passport.objects.create(
            user=user,
            display_name="Unverified",
            status=Passport.Status.UNVERIFIED,
        )
        client.force_login(user)
        response = client.get(reverse("listing_create"), follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse("passport_create")
        messages = list(response.context["messages"])
        assert any(
            "Please complete your Tenant Passport" in m.message for m in messages
        )

    def test_authenticated_pending_passport_redirects_to_dashboard(
        self, client: Client
    ) -> None:
        user = User.objects.create_user(
            email="pending@example.com",
            password="Password123!",
            display_name="Pending",
        )
        Passport.objects.create(
            user=user,
            display_name="Pending",
            status=Passport.Status.PENDING,
        )
        client.force_login(user)
        response = client.get(reverse("listing_create"), follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse("dashboard")
        messages = list(response.context["messages"])
        assert any("under review" in m.message for m in messages)

    def test_authenticated_rejected_passport_redirects_to_dashboard(
        self, client: Client
    ) -> None:
        user = User.objects.create_user(
            email="rejected@example.com",
            password="Password123!",
            display_name="Rejected",
        )
        Passport.objects.create(
            user=user,
            display_name="Rejected",
            status=Passport.Status.REJECTED,
        )
        client.force_login(user)
        response = client.get(reverse("listing_create"), follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse("dashboard")
        messages = list(response.context["messages"])
        assert any("was not approved" in m.message for m in messages)

    def test_authenticated_verified_passport_allowed(
        self, client: Client, verified_user: User
    ) -> None:
        client.force_login(verified_user)
        response = client.get(reverse("listing_create"))
        assert response.status_code == 200
        assert "Post a listing" in response.content.decode()


@pytest.mark.django_db
class TestListingCreateView:
    """Test suite for ListingCreateView form handling and active caps (Story 021)."""

    def test_get_create_view_under_cap(
        self, client: Client, verified_user: User
    ) -> None:
        client.force_login(verified_user)
        response = client.get(reverse("listing_create"))
        assert response.status_code == 200
        content = response.content.decode()
        assert response.context["cap_reached"] is False
        assert response.context["active_count"] == 0
        assert response.context["remaining_active"] == 3
        assert "0 of 3 active listings" in content
        assert "Active Listing Limit Reached" not in content
        assert "bp-upload" in content

    def test_get_create_view_at_cap(self, client: Client, verified_user: User) -> None:
        passport = verified_user.passport
        # Create 3 active listings
        for i in range(3):
            ListingService.create(
                author=passport,
                kind=ListingKind.ROOM,
                rent_bdt=12000 + i * 1000,
                rent_unit=RentUnit.PER_ROOM,
                area="Dhanmondi",
                photo_files=[create_mock_photo(f"room{i}.jpg")],
            )

        client.force_login(verified_user)
        response = client.get(reverse("listing_create"))
        assert response.status_code == 200
        assert response.context["cap_reached"] is True
        assert response.context["active_count"] == 3
        content = response.content.decode()
        assert "Active Listing Limit Reached" in content
        assert "disabled" in content

    def test_post_create_view_at_cap_blocked(
        self, client: Client, verified_user: User
    ) -> None:
        passport = verified_user.passport
        for i in range(3):
            ListingService.create(
                author=passport,
                kind=ListingKind.ROOM,
                rent_bdt=12000,
                rent_unit=RentUnit.PER_ROOM,
                area="Dhanmondi",
                photo_files=[create_mock_photo(f"cap{i}.jpg")],
            )

        client.force_login(verified_user)
        post_data = {
            "kind": ListingKind.SEAT,
            "rent_bdt": 6000,
            "rent_unit": RentUnit.PER_SEAT,
            "area": "Mirpur",
            "photos": [create_mock_photo("4th.jpg")],
        }
        response = client.post(reverse("listing_create"), post_data, follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse("listing_mine")
        messages = list(response.context["messages"])
        assert any("maximum cap of 3 active listings" in m.message for m in messages)
        assert Listing.objects.filter(author=passport).count() == 3

    def test_post_create_view_validation_error_mismatched_kind_unit(
        self, client: Client, verified_user: User
    ) -> None:
        client.force_login(verified_user)
        post_data = {
            "kind": ListingKind.SEAT,
            "rent_bdt": 6000,
            "rent_unit": RentUnit.PER_ROOM,  # Mismatch!
            "area": "Mirpur",
            "photos": [create_mock_photo("photo.jpg")],
        }
        response = client.post(reverse("listing_create"), post_data)
        assert response.status_code == 200
        assert "rent_unit" in response.context["form"].errors

    def test_post_create_view_validation_error_missing_photos(
        self, client: Client, verified_user: User
    ) -> None:
        client.force_login(verified_user)
        post_data = {
            "kind": ListingKind.ROOM,
            "rent_bdt": 15000,
            "rent_unit": RentUnit.PER_ROOM,
            "area": "Gulshan",
        }
        response = client.post(reverse("listing_create"), post_data)
        assert response.status_code == 200
        assert "photos" in response.context["form"].errors

    def test_post_create_view_success(
        self, client: Client, verified_user: User
    ) -> None:
        client.force_login(verified_user)
        photo = create_mock_photo("valid_room.jpg")
        post_data = {
            "kind": ListingKind.ROOM,
            "rent_bdt": 16000,
            "rent_unit": RentUnit.PER_ROOM,
            "area": "Gulshan",
            "body": "Spacious master bedroom with attached bath and balcony.",
            "pref_gender": PreferredGender.MALE,
            "pref_smoking": PreferredSmoking.NO,
            "pref_sleep": PreferredSleepSchedule.EARLY_BIRD,
            "pref_occupation": [PreferredOccupation.PRIVATE_JOB],
            "photos": [photo],
        }
        response = client.post(reverse("listing_create"), post_data, follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse("listing_mine")
        messages = list(response.context["messages"])
        assert any("posted successfully" in m.message for m in messages)

        listing = Listing.objects.get(author=verified_user.passport)
        assert listing.rent_bdt == 16000
        assert listing.photos.count() == 1
        assert listing.is_active is True


@pytest.mark.django_db
class TestListerDashboardView:
    """Test suite for ListerDashboardView tabs and cap meter (Story 022)."""

    def test_dashboard_empty_state(self, client: Client, verified_user: User) -> None:
        client.force_login(verified_user)
        response = client.get(reverse("listing_mine"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "No Active Listings" in content
        assert "Post Your First Listing" in content

    def test_dashboard_multi_tenant_isolation(
        self,
        client: Client,
        verified_user: User,
        other_verified_user: User,
    ) -> None:
        # Create listing for verified_user
        res_a = ListingService.create(
            author=verified_user.passport,
            kind=ListingKind.ROOM,
            rent_bdt=14000,
            rent_unit=RentUnit.PER_ROOM,
            area="Dhanmondi",
            photo_files=[create_mock_photo("a.jpg")],
        )
        # Create listing for other_verified_user
        res_b = ListingService.create(
            author=other_verified_user.passport,
            kind=ListingKind.SEAT,
            rent_bdt=5000,
            rent_unit=RentUnit.PER_SEAT,
            area="Uttara",
            photo_files=[create_mock_photo("b.jpg")],
        )

        client.force_login(verified_user)
        response = client.get(reverse("listing_mine"))
        assert response.status_code == 200
        content = response.content.decode()

        # Own listing is present
        assert "৳14000" in content or "14,000" in content
        assert "Dhanmondi" in content

        # Other user's listing is completely isolated
        assert "Uttara" not in content
        assert res_b["listing"].pk != res_a["listing"].pk

    def test_dashboard_tab_filtering_active_vs_inactive(
        self, client: Client, verified_user: User
    ) -> None:
        passport = verified_user.passport
        # Active listing
        ListingService.create(
            author=passport,
            kind=ListingKind.ROOM,
            rent_bdt=15000,
            rent_unit=RentUnit.PER_ROOM,
            area="Banani",
            photo_files=[create_mock_photo("banani.jpg")],
        )
        # Withdrawn listing
        res_withdrawn = ListingService.create(
            author=passport,
            kind=ListingKind.SEAT,
            rent_bdt=5500,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
            photo_files=[create_mock_photo("mirpur.jpg")],
        )
        ListingService.withdraw(listing=res_withdrawn["listing"], actor=verified_user)

        client.force_login(verified_user)

        # Tab: Active (default)
        response_active = client.get(reverse("listing_mine") + "?tab=active")
        assert response_active.status_code == 200
        content_active = response_active.content.decode()
        assert "Banani" in content_active
        assert "Mirpur" not in content_active
        assert response_active.context["active_count"] == 1
        assert response_active.context["inactive_count"] == 1

        # Tab: Inactive (withdrawn & archived)
        response_inactive = client.get(reverse("listing_mine") + "?tab=inactive")
        assert response_inactive.status_code == 200
        content_inactive = response_inactive.content.decode()
        assert "Mirpur" in content_inactive
        assert "Banani" not in content_inactive


@pytest.mark.django_db
class TestListingEditView:
    """Test suite for ListingEditView locked fields and authorization (Story 023)."""

    @pytest.fixture
    def authored_listing(self, verified_user: User) -> Listing:
        res = ListingService.create(
            author=verified_user.passport,
            kind=ListingKind.ROOM,
            rent_bdt=18000,
            rent_unit=RentUnit.PER_ROOM,
            area="Dhanmondi",
            body="Original host note",
            photo_files=[create_mock_photo("room_orig.jpg")],
        )
        return res["listing"]

    def test_edit_view_get_owner_allowed(
        self, client: Client, verified_user: User, authored_listing: Listing
    ) -> None:
        client.force_login(verified_user)
        url = reverse("listing_edit", kwargs={"pk": authored_listing.pk})
        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Edit Listing Terms" in content
        assert "Locked Listing Identity" in content
        assert "Dhanmondi" in content
        assert "Room" in content

    def test_edit_view_get_non_owner_forbidden(
        self, client: Client, other_verified_user: User, authored_listing: Listing
    ) -> None:
        client.force_login(other_verified_user)
        url = reverse("listing_edit", kwargs={"pk": authored_listing.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_edit_view_post_updates_mutable_fields(
        self, client: Client, verified_user: User, authored_listing: Listing
    ) -> None:
        client.force_login(verified_user)
        url = reverse("listing_edit", kwargs={"pk": authored_listing.pk})
        post_data = {
            "rent_bdt": 20000,
            "rent_unit": RentUnit.PER_ROOM,
            "body": "Updated description with new terms.",
            "pref_gender": PreferredGender.ANY,
            "pref_smoking": PreferredSmoking.NO,
            "pref_sleep": PreferredSleepSchedule.FLEXIBLE,
            "pref_occupation": [PreferredOccupation.STUDENT],
        }
        response = client.post(url, post_data, follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse("listing_mine")

        authored_listing.refresh_from_db()
        assert authored_listing.rent_bdt == 20000
        assert authored_listing.body == "Updated description with new terms."
        assert authored_listing.kind == ListingKind.ROOM  # Preserved!
        assert authored_listing.area == "Dhanmondi"  # Preserved!


@pytest.mark.django_db
class TestListingWithdrawView:
    """Test suite for ListingWithdrawView modal action and cap decrement (Story 023)."""

    @pytest.fixture
    def active_listing(self, verified_user: User) -> Listing:
        res = ListingService.create(
            author=verified_user.passport,
            kind=ListingKind.SEAT,
            rent_bdt=6000,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
            photo_files=[create_mock_photo("seat.jpg")],
        )
        return res["listing"]

    def test_withdraw_get_redirects_to_mine(
        self, client: Client, verified_user: User, active_listing: Listing
    ) -> None:
        client.force_login(verified_user)
        url = reverse("listing_withdraw", kwargs={"pk": active_listing.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == reverse("listing_mine")

    def test_withdraw_post_non_owner_forbidden(
        self, client: Client, other_verified_user: User, active_listing: Listing
    ) -> None:
        client.force_login(other_verified_user)
        url = reverse("listing_withdraw", kwargs={"pk": active_listing.pk})
        response = client.post(url)
        assert response.status_code == 403

    def test_withdraw_post_owner_success(
        self, client: Client, verified_user: User, active_listing: Listing
    ) -> None:
        client.force_login(verified_user)
        url = reverse("listing_withdraw", kwargs={"pk": active_listing.pk})
        response = client.post(url, follow=True)
        assert response.status_code == 200
        assert response.redirect_chain[0][0] == reverse("listing_mine")

        active_listing.refresh_from_db()
        assert active_listing.is_active is False
        assert active_listing.is_withdrawn is True
        assert active_listing.withdrawn_at is not None

        messages = list(response.context["messages"])
        assert any("withdrawn" in m.message for m in messages)
