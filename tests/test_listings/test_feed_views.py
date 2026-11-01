"""Tests for ListingFeedView and ListingDetailView (Stories 026, 027, 028)."""

from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
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
from apps.listings.models import Listing, ListingPhoto
from apps.passports.models import LifestyleProfile, Passport


@pytest.mark.django_db
class TestListingDiscoveryViews:
    """Test suite for public listing feed, filter drawer, and gated detail page."""

    @pytest.fixture
    def lister_user(self) -> User:
        return User.objects.create_user(
            email="tanvir_feed_ui@example.com",
            password="Password123!",
            display_name="Tanvir H.",
            phone_number="+8801712345678",
        )

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
    def verified_seeker(self) -> User:
        user = User.objects.create_user(
            email="seeker_ui_verified@example.com",
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
            budget_max=6000,
        )
        return user

    @pytest.fixture
    def unverified_seeker(self) -> User:
        user = User.objects.create_user(
            email="seeker_ui_unverified@example.com",
            password="Password123!",
            display_name="Seeker Unverified",
        )
        Passport.objects.create(
            user=user,
            display_name="Seeker Unverified",
            status=Passport.Status.UNVERIFIED,
        )
        return user

    @pytest.fixture
    def sample_listings(self, lister_passport: Passport) -> list[Listing]:
        l1 = Listing.objects.create(
            author=lister_passport,
            kind=ListingKind.SEAT,
            rent_bdt=4500,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
            body="Quiet mess, 2-min walk to circle.",
            pref_gender=PreferredGender.MALE,
            pref_smoking=PreferredSmoking.NO,
            pref_sleep=PreferredSleepSchedule.EARLY_BIRD,
            pref_occupation=[PreferredOccupation.STUDENT],
        )
        ListingPhoto.objects.create(
            listing=l1, photo_path="listings/photos/photo1.jpg", order=0
        )
        ListingPhoto.objects.create(
            listing=l1, photo_path="listings/photos/photo2.jpg", order=1
        )

        l2 = Listing.objects.create(
            author=lister_passport,
            kind=ListingKind.ROOM,
            rent_bdt=12000,
            rent_unit=RentUnit.PER_ROOM,
            area="Banani",
            body="Private master bedroom with attached bath.",
            pref_gender=PreferredGender.FEMALE,
            pref_smoking=PreferredSmoking.NO,
            pref_sleep=PreferredSleepSchedule.FLEXIBLE,
            pref_occupation=[PreferredOccupation.PRIVATE_JOB],
        )
        return [l1, l2]

    # --- FEED TESTS (Story 026 & Story 027) ---

    def test_anonymous_access_to_feed(
        self, client: Client, sample_listings: list[Listing]
    ) -> None:
        """Feed is publicly accessible without authentication (AD-8)."""
        response = client.get(reverse("listing_feed"))
        assert response.status_code == 200
        assert "Find verified rooms & seats in Dhaka" in response.content.decode()
        assert "Mirpur" in response.content.decode()
        assert "Banani" in response.content.decode()
        # Verify anonymous cards show locked lifestyle hint
        assert "Verify to see lifestyle fit" in response.content.decode()
        # Verify footer is rendered on public feed
        templates_used = [t.name for t in response.templates if t.name]
        assert "basha/partials/footer.html" in templates_used
        assert "Basha Pass · Dhaka" in response.content.decode()

    def test_feed_renders_absolute_media_urls_for_photos(
        self, client: Client, sample_listings: list[Listing]
    ) -> None:
        """Photo URLs on cards are properly prefixed with /media/ (zero 404)."""
        response = client.get(reverse("listing_feed"))
        assert response.status_code == 200
        projections = response.context["projections"]
        mirpur = next(p for p in projections if p.area == "Mirpur")
        assert mirpur.primary_photo_url is not None
        assert mirpur.primary_photo_url.startswith("/media/")
        assert mirpur.primary_photo_url == "/media/listings/photos/photo1.jpg"
        assert len(mirpur.photos) == 2
        assert mirpur.photos[0].url == "/media/listings/photos/photo1.jpg"
        assert mirpur.photos[1].url == "/media/listings/photos/photo2.jpg"

    def test_media_file_served_via_http_client(
        self,
        client: Client,
        sample_listings: list[Listing],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """HTTP GET to /media/<photo_path> returns 200 when file exists on disk."""
        from apps.listings.services.storage import ListingPhotoStorageService

        listing = sample_listings[0]
        photo = listing.photos.first()
        assert photo is not None

        # Create physical test file
        root = ListingPhotoStorageService.get_public_root()
        file_path = root / photo.photo_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01")

        try:
            # Enable DEBUG and reload url patterns for static serving
            monkeypatch.setattr("django.conf.settings.DEBUG", True)
            response = client.get(photo.url)
            assert response.status_code == 200
        finally:
            if file_path.exists():
                file_path.unlink()

    def test_verified_seeker_views_compatibility_dots(
        self,
        client: Client,
        verified_seeker: User,
        sample_listings: list[Listing],
    ) -> None:
        """Verified seeker receives 0-6 score dots on cards (Story 027)."""
        client.force_login(verified_seeker)
        response = client.get(reverse("listing_feed"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "matches 6 of 6 preferences" in content

    def test_feed_area_filter(
        self, client: Client, sample_listings: list[Listing]
    ) -> None:
        """Filtering by area parameter shows only matching listings."""
        response = client.get(reverse("listing_feed") + "?area=Mirpur")
        assert response.status_code == 200
        projections = response.context["projections"]
        assert len(projections) == 1
        assert projections[0].area == "Mirpur"

    def test_feed_budget_filter(
        self, client: Client, sample_listings: list[Listing]
    ) -> None:
        """Filtering by budget range refines results."""
        response = client.get(
            reverse("listing_feed") + "?budget_min=10000&budget_max=15000"
        )
        assert response.status_code == 200
        projections = response.context["projections"]
        assert len(projections) == 1
        assert projections[0].rent_bdt == 12000

    def test_feed_kind_filter(
        self, client: Client, sample_listings: list[Listing]
    ) -> None:
        """Filtering by kind=seat shows only seat listings."""
        response = client.get(reverse("listing_feed") + "?kind=seat")
        assert response.status_code == 200
        projections = response.context["projections"]
        assert len(projections) == 1
        assert projections[0].kind == ListingKind.SEAT

    def test_feed_sorting(self, client: Client, sample_listings: list[Listing]) -> None:
        """Feed respects sort parameter (rent_desc, rent_asc)."""
        response = client.get(reverse("listing_feed") + "?sort=rent_desc")
        assert response.status_code == 200
        projections = response.context["projections"]
        assert projections[0].rent_bdt == 12000
        assert projections[1].rent_bdt == 4500

    def test_feed_empty_state_rendered(
        self, client: Client, sample_listings: list[Listing]
    ) -> None:
        """Empty state is displayed when no listings match filter criteria."""
        response = client.get(reverse("listing_feed") + "?area=Uttara")
        assert response.status_code == 200
        content = response.content.decode()
        assert "No listings found matching your criteria" in content
        assert "Clear all filters" in content

    def test_feed_htmx_partial_update(
        self, client: Client, sample_listings: list[Listing]
    ) -> None:
        """HTMX request returns partial feed_results.html without full base layout."""
        response = client.get(
            reverse("listing_feed"),
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        templates_used = [t.name for t in response.templates if t.name]
        assert "listings/partials/feed_results.html" in templates_used
        assert "listings/feed.html" not in templates_used
        assert "basha/partials/navbar.html" not in templates_used
        content = response.content.decode()
        assert 'id="feed-container"' in content
        assert "Showing <strong>2</strong> active listings" in content

    def test_feed_htmx_filtered_results(
        self, client: Client, sample_listings: list[Listing]
    ) -> None:
        """HTMX filter request updates results, counts, and active filter pill."""
        response = client.get(
            reverse("listing_feed") + "?area=Mirpur&budget_max=6000",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert 'id="feed-container"' in content
        assert "Showing <strong>1</strong> active listing" in content
        assert "Mirpur" in content
        assert "Banani" not in content
        # Active filter count should reflect 1 area + 1 budget filter = 2
        assert response.context["active_filter_count"] == 2

    # --- DETAIL VIEW TESTS (Story 028) ---

    def test_anonymous_access_to_detail_locks_contact(
        self, client: Client, sample_listings: list[Listing]
    ) -> None:
        """Anonymous visitor views listing detail with locked contact (AD-3)."""
        listing = sample_listings[0]
        url = reverse("listing_detail", kwargs={"pk": listing.id})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        # Headline and details visible
        assert "Mirpur" in content
        assert "৳4,500" in content
        assert "Verify to see contact info" in content

        # CRITICAL PII CHECK: Lister's email and phone MUST NOT be anywhere in DOM
        assert "tanvir_feed_ui@example.com" not in content
        assert "+8801712345678" not in content
        assert "01712345678" not in content

        # Verify footer is rendered on public detail page
        templates_used = [t.name for t in response.templates if t.name]
        assert "basha/partials/footer.html" in templates_used
        assert "Basha Pass · Dhaka" in content

    def test_unverified_seeker_access_to_detail_locks_contact(
        self,
        client: Client,
        unverified_seeker: User,
        sample_listings: list[Listing],
    ) -> None:
        """Unverified authenticated seeker sees locked contact panel without PII."""
        client.force_login(unverified_seeker)
        listing = sample_listings[0]
        url = reverse("listing_detail", kwargs={"pk": listing.id})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()

        assert "Verify to see contact info" in content
        assert "Start verification" in content
        assert "tanvir_feed_ui@example.com" not in content
        assert "+8801712345678" not in content

    def test_verified_seeker_access_to_detail_unlocks_contact_and_audits(
        self,
        client: Client,
        verified_seeker: User,
        sample_listings: list[Listing],
    ) -> None:
        """Verified seeker sees contact channels and creates AuditEntry (AD-15)."""
        client.force_login(verified_seeker)
        listing = sample_listings[0]
        url = reverse("listing_detail", kwargs={"pk": listing.id})

        initial_audits = AuditEntry.objects.filter(
            target_id=listing.id, action="contact_viewed"
        ).count()

        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()

        # Unlocked contact details
        assert "tanvir_feed_ui@example.com" in content
        assert "+8801712345678" in content
        assert "tel:+8801712345678" in content
        assert "copy-phone-btn" in content
        assert 'data-phone="+8801712345678"' in content
        assert "Off-platform contact" in content
        assert "Reach Tanvir H. directly" in content

        # Check compatibility breakdown checklist
        assert "Lifestyle Compatibility" in content
        assert "6 of 6 match" in content

        # Check AuditEntry recorded
        new_audits = AuditEntry.objects.filter(
            target_id=listing.id, action="contact_viewed"
        ).count()
        assert new_audits == initial_audits + 1

        audit = AuditEntry.objects.filter(
            target_id=listing.id, action="contact_viewed"
        ).latest("timestamp")
        assert audit.actor_id == verified_seeker.id

    def test_author_accesses_own_detail_view_without_audit(
        self, client: Client, lister_user: User, sample_listings: list[Listing]
    ) -> None:
        """Lister viewing own listing sees contact without emitting audit entry."""
        client.force_login(lister_user)
        listing = sample_listings[0]
        url = reverse("listing_detail", kwargs={"pk": listing.id})

        initial_audits = AuditEntry.objects.filter(
            target_id=listing.id, action="contact_viewed"
        ).count()

        response = client.get(url)
        assert response.status_code == 200
        content = response.content.decode()

        # Author can see their contact
        assert "tanvir_feed_ui@example.com" in content

        # No external audit entry recorded
        new_audits = AuditEntry.objects.filter(
            target_id=listing.id, action="contact_viewed"
        ).count()
        assert new_audits == initial_audits

    def test_nonexistent_listing_detail_returns_404(self, client: Client) -> None:
        """Request for unknown listing UUID returns 404."""
        import uuid

        random_id = uuid.uuid4()
        response = client.get(reverse("listing_detail", kwargs={"pk": random_id}))
        assert response.status_code == 404

    def test_withdrawn_listing_detail_returns_404_for_public(
        self,
        client: Client,
        lister_passport: Passport,
        verified_seeker: User,
    ) -> None:
        """Withdrawn listing returns 404 for non-author visitors."""
        withdrawn_listing = Listing.objects.create(
            author=lister_passport,
            kind=ListingKind.SEAT,
            rent_bdt=5000,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
            withdrawn_at=timezone.now() - timedelta(hours=1),
        )

        client.force_login(verified_seeker)
        response = client.get(
            reverse("listing_detail", kwargs={"pk": withdrawn_listing.id})
        )
        assert response.status_code == 404

    def test_verified_seeker_access_to_detail_without_phone_shows_fallback(
        self,
        client: Client,
        lister_user: User,
        verified_seeker: User,
        sample_listings: list[Listing],
    ) -> None:
        """When host has no phone, verified viewer sees clean fallback message."""
        lister_user.phone_number = None
        lister_user.save(update_fields=["phone_number"])

        client.force_login(verified_seeker)
        listing = sample_listings[0]
        url = reverse("listing_detail", kwargs={"pk": listing.id})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "tanvir_feed_ui@example.com" in content
        assert "Not provided by host" in content
        assert "tel:" not in content
        assert "copy-phone-btn" not in content

    def test_author_without_phone_sees_add_phone_prompt(
        self,
        client: Client,
        lister_user: User,
        sample_listings: list[Listing],
    ) -> None:
        """Host viewing their listing without phone sees prompt to add one."""
        lister_user.phone_number = None
        lister_user.save(update_fields=["phone_number"])

        client.force_login(lister_user)
        listing = sample_listings[0]
        url = reverse("listing_detail", kwargs={"pk": listing.id})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Not provided by host" in content
        assert "Add phone" in content
        assert reverse("listing_edit", kwargs={"pk": listing.id}) in content
