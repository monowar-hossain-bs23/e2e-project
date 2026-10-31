"""Tests for ListingFeedQuery read model and audit logging (Story 025, AD-12, AD-15)."""

from datetime import timedelta

import pytest
from django.utils import timezone
from pytest_django.asserts import assertNumQueries

from apps.accounts.models import User
from apps.audit.models import AuditEntry
from apps.listings.constants import (
    ListingKind,
    PreferredGender,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentUnit,
)
from apps.listings.models import Listing, ListingPhoto
from apps.listings.services.feed_query import ListingFeedQuery
from apps.passports.models import LifestyleProfile, Passport


@pytest.mark.django_db
class TestListingFeedQuery:
    """Test suite for ListingFeedQuery discovery query, filter, sort, audit."""

    @pytest.fixture
    def author_user(self) -> User:
        return User.objects.create_user(
            email="lister_feed@example.com",
            password="Password123!",
            display_name="Feed Author",
            phone_number="+8801700000000",
        )

    @pytest.fixture
    def author_passport(self, author_user: User) -> Passport:
        passport = Passport.objects.create(
            user=author_user,
            display_name="Feed Author",
            status=Passport.Status.VERIFIED,
        )
        LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.STUDENT,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Mirpur", "Banani"],
            budget_min=4000,
            budget_max=10000,
        )
        return passport

    @pytest.fixture
    def verified_seeker(self) -> User:
        user = User.objects.create_user(
            email="seeker_verified_feed@example.com",
            password="Password123!",
            display_name="Seeker Verified",
            phone_number="+8801811111111",
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
    def sample_listings(self, author_passport: Passport) -> list[Listing]:
        """Create a diverse inventory of listings for search and filter testing."""
        now = timezone.now()

        # 1. Mirpur Seat - ৳4,500
        l1 = Listing.objects.create(
            author=author_passport,
            kind=ListingKind.SEAT,
            rent_bdt=4500,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
            body="Quiet shared seat near campus.",
            pref_gender=PreferredGender.MALE,
            pref_smoking=PreferredSmoking.NO,
            pref_sleep=PreferredSleepSchedule.EARLY_BIRD,
            pref_occupation=["student"],
        )
        ListingPhoto.objects.create(listing=l1, photo_path="listings/p1.jpg", order=0)

        # 2. Banani Room - ৳15,000
        l2 = Listing.objects.create(
            author=author_passport,
            kind=ListingKind.ROOM,
            rent_bdt=15000,
            rent_unit=RentUnit.PER_ROOM,
            area="Banani",
            body="Private room in upscale flat.",
            pref_gender=PreferredGender.ANY,
            pref_smoking=PreferredSmoking.NO,
            pref_sleep=PreferredSleepSchedule.FLEXIBLE,
            pref_occupation=["private_job"],
        )

        # 3. Dhanmondi Seat - ৳6,000
        l3 = Listing.objects.create(
            author=author_passport,
            kind=ListingKind.SEAT,
            rent_bdt=6000,
            rent_unit=RentUnit.PER_SEAT,
            area="Dhanmondi",
            body="Mess seat for working professional.",
            pref_gender=PreferredGender.MALE,
            pref_smoking=PreferredSmoking.YES,
            pref_sleep=PreferredSleepSchedule.NIGHT_OWL,
            pref_occupation=["any"],
        )

        # 4. Withdrawn listing (should be excluded)
        l_withdrawn = Listing.objects.create(
            author=author_passport,
            kind=ListingKind.SEAT,
            rent_bdt=3500,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
            withdrawn_at=now,
        )

        # 5. Archived listing (should be excluded)
        l_archived = Listing.objects.create(
            author=author_passport,
            kind=ListingKind.ROOM,
            rent_bdt=12000,
            rent_unit=RentUnit.PER_ROOM,
            area="Uttara",
            archived_at=now,
        )

        # 6. Stale listing older than 60 days (should be excluded)
        l_stale = Listing.objects.create(
            author=author_passport,
            kind=ListingKind.SEAT,
            rent_bdt=4000,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
        )
        Listing.objects.filter(pk=l_stale.pk).update(
            created_at=now - timedelta(days=65)
        )

        return [l1, l2, l3, l_withdrawn, l_archived, l_stale]

    def test_feed_excludes_withdrawn_archived_and_stale(
        self, sample_listings: list[Listing]
    ) -> None:
        """Feed returns only active, non-archived, fresh (<60d) listings."""
        result = ListingFeedQuery.for_viewer(viewer=None)

        assert result["total_count"] == 3
        ids = [p.id for p in result["projections"]]
        assert sample_listings[0].id in ids  # l1
        assert sample_listings[1].id in ids  # l2
        assert sample_listings[2].id in ids  # l3
        assert sample_listings[3].id not in ids  # withdrawn
        assert sample_listings[4].id not in ids  # archived
        assert sample_listings[5].id not in ids  # stale > 60d

    def test_feed_sort_order(self, sample_listings: list[Listing]) -> None:
        """Sorting applies rent_asc, rent_desc, or newest correctly."""
        # Rent asc: 4500, 6000, 15000
        asc_res = ListingFeedQuery.for_viewer(viewer=None, sort="rent_asc")
        asc_rents = [p.rent_bdt for p in asc_res["projections"]]
        assert asc_rents == [4500, 6000, 15000]

        # Rent desc: 15000, 6000, 4500
        desc_res = ListingFeedQuery.for_viewer(viewer=None, sort="rent_desc")
        desc_rents = [p.rent_bdt for p in desc_res["projections"]]
        assert desc_rents == [15000, 6000, 4500]

    def test_feed_filter_by_area(self, sample_listings: list[Listing]) -> None:
        """Filtering by area narrows results."""
        res_mirpur = ListingFeedQuery.for_viewer(viewer=None, areas=["Mirpur"])
        assert res_mirpur["total_count"] == 1
        assert res_mirpur["projections"][0].area == "Mirpur"

        res_multi = ListingFeedQuery.for_viewer(viewer=None, areas=["Mirpur", "Banani"])
        assert res_multi["total_count"] == 2

    def test_feed_filter_by_budget_range(self, sample_listings: list[Listing]) -> None:
        """Filtering by budget min and max works accurately."""
        res = ListingFeedQuery.for_viewer(
            viewer=None, budget_min=5000, budget_max=10000
        )
        assert res["total_count"] == 1
        assert res["projections"][0].rent_bdt == 6000

    def test_feed_filter_by_kind_and_unit(self, sample_listings: list[Listing]) -> None:
        """Filtering by kind=room returns only rooms."""
        res = ListingFeedQuery.for_viewer(viewer=None, kind="room")
        assert res["total_count"] == 1
        assert res["projections"][0].kind == "room"

    def test_feed_filter_by_lifestyle_preferences(
        self, sample_listings: list[Listing]
    ) -> None:
        """Lifestyle filters match exact preference or 'any'."""
        # Non-smoker: l1 (pref=no), l2 (pref=no)
        res_non_smoke = ListingFeedQuery.for_viewer(viewer=None, smoking="no")
        assert res_non_smoke["total_count"] == 2

        # Female: matches l2 (pref=any) only
        res_female = ListingFeedQuery.for_viewer(viewer=None, gender="female")
        assert res_female["total_count"] == 1
        assert res_female["projections"][0].id == sample_listings[1].id

    def test_feed_filter_by_occupation(self, sample_listings: list[Listing]) -> None:
        """Occupation filter matches occupations in list or 'any'."""
        # Student matches l1 (pref=['student']) and l3 (pref=['any'])
        res = ListingFeedQuery.for_viewer(viewer=None, occupations=["student"])
        assert res["total_count"] == 2
        ids = [p.id for p in res["projections"]]
        assert sample_listings[0].id in ids
        assert sample_listings[2].id in ids

    def test_feed_compatibility_hint_attached_for_verified_seeker(
        self, verified_seeker: User, sample_listings: list[Listing]
    ) -> None:
        """Verified seeker receives integer 0-6 compatibility hint on listings."""
        res = ListingFeedQuery.for_viewer(viewer=verified_seeker)

        # Mirpur listing (l1): matches male, no-smoke, sleep, student, Mirpur -> 6/6
        l1_proj = next(p for p in res["projections"] if p.id == sample_listings[0].id)
        assert l1_proj.compatibility_hint == 6

        # Banani listing (l2): rent 15000 > 6000, mismatch on area/occupation
        l2_proj = next(p for p in res["projections"] if p.id == sample_listings[1].id)
        assert l2_proj.compatibility_hint is not None
        assert l2_proj.compatibility_hint < 6

    def test_feed_pagination(self, author_passport: Passport) -> None:
        """Pagination slices results into pages of specified size."""
        # Create 15 active listings
        for i in range(15):
            Listing.objects.create(
                author=author_passport,
                kind=ListingKind.SEAT,
                rent_bdt=4000 + i * 100,
                rent_unit=RentUnit.PER_SEAT,
                area="Mirpur",
            )

        res_p1 = ListingFeedQuery.for_viewer(viewer=None, page=1, page_size=10)
        assert len(res_p1["projections"]) == 10
        assert res_p1["total_count"] >= 15
        assert res_p1["page_obj"].has_next() is True

        res_p2 = ListingFeedQuery.for_viewer(viewer=None, page=2, page_size=10)
        assert len(res_p2["projections"]) >= 5

    def test_feed_zero_n_plus_one_queries(self, author_passport: Passport) -> None:
        """Batch query uses constant number of SQL statements."""
        for i in range(10):
            item = Listing.objects.create(
                author=author_passport,
                kind=ListingKind.SEAT,
                rent_bdt=5000 + i * 50,
                rent_unit=RentUnit.PER_SEAT,
                area="Mirpur",
            )
            ListingPhoto.objects.create(listing=item, photo_path=f"p{i}.jpg", order=0)

        # Run query and verify fixed query count (1 count, 1 select_related, 2 prefetch)
        with assertNumQueries(4):
            res = ListingFeedQuery.for_viewer(viewer=None, page_size=10)
            # Iterate through all items to verify zero extra queries
            for proj in res["projections"]:
                _ = proj.author_display_name
                _ = len(proj.photos)
                _ = proj.primary_photo_url

    def test_detail_query_verified_viewer_emits_audit(
        self, verified_seeker: User, sample_listings: list[Listing]
    ) -> None:
        """Viewing detail as verified viewer unlocks contact and records AuditEntry."""
        listing = sample_listings[0]
        initial_audits = AuditEntry.objects.filter(
            target_id=listing.id, action="contact_viewed"
        ).count()

        proj = ListingFeedQuery.get_detail_for_viewer(
            viewer=verified_seeker, listing_id=listing.id
        )

        assert proj is not None
        assert proj.is_contact_locked is False
        assert proj.lister_email == "lister_feed@example.com"
        assert proj.lister_phone == "+8801700000000"

        # Check AuditEntry
        new_audits = AuditEntry.objects.filter(
            target_id=listing.id, action="contact_viewed"
        ).count()
        assert new_audits == initial_audits + 1

    def test_detail_query_author_does_not_emit_external_audit(
        self, author_user: User, sample_listings: list[Listing]
    ) -> None:
        """Author viewing own listing does not emit contact_viewed audit entry."""
        listing = sample_listings[0]
        initial_audits = AuditEntry.objects.filter(
            target_id=listing.id, action="contact_viewed"
        ).count()

        proj = ListingFeedQuery.get_detail_for_viewer(
            viewer=author_user, listing_id=listing.id
        )

        assert proj is not None
        assert proj.is_contact_locked is False

        new_audits = AuditEntry.objects.filter(
            target_id=listing.id, action="contact_viewed"
        ).count()
        assert new_audits == initial_audits

    def test_detail_query_withdrawn_returns_none_for_public(
        self, verified_seeker: User, sample_listings: list[Listing]
    ) -> None:
        """Withdrawn listing returns None when accessed by public seekers."""
        withdrawn_listing = sample_listings[3]
        proj = ListingFeedQuery.get_detail_for_viewer(
            viewer=verified_seeker, listing_id=withdrawn_listing.id
        )
        assert proj is None
