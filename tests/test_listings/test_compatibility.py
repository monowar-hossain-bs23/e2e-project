"""Tests for CompatibilityEngine lifestyle heuristic (Story 025, AD-12)."""

from types import SimpleNamespace

import pytest

from apps.listings.constants import (
    ListingKind,
    PreferredGender,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentUnit,
)
from apps.listings.models import Listing
from apps.listings.services.compatibility import CompatibilityEngine


@pytest.mark.django_db
class TestCompatibilityEngine:
    """Test suite for 6-axis lifestyle compatibility scoring."""

    @pytest.fixture
    def base_listing(self, db: None) -> Listing:
        """Create a mock-style listing instance for compatibility testing."""
        # Unsaved instance is sufficient for CompatibilityEngine unit tests
        return Listing(
            kind=ListingKind.SEAT,
            rent_bdt=4500,
            rent_unit=RentUnit.PER_SEAT,
            area="Mirpur",
            pref_gender=PreferredGender.MALE,
            pref_smoking=PreferredSmoking.NO,
            pref_sleep=PreferredSleepSchedule.EARLY_BIRD,
            pref_occupation=["student"],
        )

    def test_evaluate_perfect_six_axis_match(self, base_listing: Listing) -> None:
        """Seeker matching all 6 axes gets score 6 and all true breakdown."""
        seeker_profile = SimpleNamespace(
            gender="male",
            smoking="no",
            sleep_schedule="early_bird",
            occupation="student",
            area_preference=["Mirpur", "Uttara"],
            budget_max=5000,
        )

        score, breakdown = CompatibilityEngine.evaluate(seeker_profile, base_listing)

        assert score == 6
        assert breakdown["gender"] is True
        assert breakdown["smoking"] is True
        assert breakdown["sleep"] is True
        assert breakdown["occupation"] is True
        assert breakdown["area"] is True
        assert breakdown["budget"] is True

    def test_evaluate_gender_axis_any_always_matches(
        self, base_listing: Listing
    ) -> None:
        """Listing with pref_gender='any' matches any seeker gender."""
        base_listing.pref_gender = PreferredGender.ANY
        female_seeker = SimpleNamespace(
            gender="female",
            smoking="no",
            sleep_schedule="early_bird",
            occupation="student",
            area_preference=["Mirpur"],
            budget_max=5000,
        )

        score, breakdown = CompatibilityEngine.evaluate(female_seeker, base_listing)
        assert breakdown["gender"] is True

    def test_evaluate_gender_mismatch(self, base_listing: Listing) -> None:
        """Listing pref_gender='male' mismatches female seeker."""
        base_listing.pref_gender = PreferredGender.MALE
        female_seeker = SimpleNamespace(
            gender="female",
            smoking="no",
            sleep_schedule="early_bird",
            occupation="student",
            area_preference=["Mirpur"],
            budget_max=5000,
        )

        score, breakdown = CompatibilityEngine.evaluate(female_seeker, base_listing)
        assert breakdown["gender"] is False
        assert score == 5

    def test_evaluate_smoking_axis(self, base_listing: Listing) -> None:
        """Smoking axis checks exact match or 'any'."""
        base_listing.pref_smoking = PreferredSmoking.NO
        smoker_seeker = SimpleNamespace(
            gender="male",
            smoking="yes",
            sleep_schedule="early_bird",
            occupation="student",
            area_preference=["Mirpur"],
            budget_max=5000,
        )
        score, breakdown = CompatibilityEngine.evaluate(smoker_seeker, base_listing)
        assert breakdown["smoking"] is False

        # Any matches
        base_listing.pref_smoking = PreferredSmoking.ANY
        score_any, breakdown_any = CompatibilityEngine.evaluate(
            smoker_seeker, base_listing
        )
        assert breakdown_any["smoking"] is True

    def test_evaluate_sleep_schedule_axis(self, base_listing: Listing) -> None:
        """Sleep schedule checks exact match or 'flexible'."""
        base_listing.pref_sleep = PreferredSleepSchedule.EARLY_BIRD
        night_owl_seeker = SimpleNamespace(
            gender="male",
            smoking="no",
            sleep_schedule="night_owl",
            occupation="student",
            area_preference=["Mirpur"],
            budget_max=5000,
        )
        score, breakdown = CompatibilityEngine.evaluate(night_owl_seeker, base_listing)
        assert breakdown["sleep"] is False

        # Flexible matches
        base_listing.pref_sleep = PreferredSleepSchedule.FLEXIBLE
        _, breakdown_flex = CompatibilityEngine.evaluate(night_owl_seeker, base_listing)
        assert breakdown_flex["sleep"] is True

    def test_evaluate_occupation_axis(self, base_listing: Listing) -> None:
        """Occupation matches if seeker occupation in list or listing has 'any'."""
        base_listing.pref_occupation = ["student", "private_job"]
        freelancer = SimpleNamespace(
            gender="male",
            smoking="no",
            sleep_schedule="early_bird",
            occupation="freelancer",
            area_preference=["Mirpur"],
            budget_max=5000,
        )
        _, breakdown = CompatibilityEngine.evaluate(freelancer, base_listing)
        assert breakdown["occupation"] is False

        base_listing.pref_occupation = ["any"]
        _, breakdown_any = CompatibilityEngine.evaluate(freelancer, base_listing)
        assert breakdown_any["occupation"] is True

    def test_evaluate_area_axis(self, base_listing: Listing) -> None:
        """Area matches if listing area is in seeker's preferred area list."""
        base_listing.area = "Mirpur"
        dhanmondi_seeker = SimpleNamespace(
            gender="male",
            smoking="no",
            sleep_schedule="early_bird",
            occupation="student",
            area_preference=["Dhanmondi", "Banani"],
            budget_max=5000,
        )
        _, breakdown = CompatibilityEngine.evaluate(dhanmondi_seeker, base_listing)
        assert breakdown["area"] is False

        dhanmondi_seeker.area_preference.append("Mirpur")
        _, breakdown_match = CompatibilityEngine.evaluate(
            dhanmondi_seeker, base_listing
        )
        assert breakdown_match["area"] is True

    def test_evaluate_budget_axis(self, base_listing: Listing) -> None:
        """Budget matches if listing rent_bdt <= seeker budget_max."""
        base_listing.rent_bdt = 5000
        budget_tight_seeker = SimpleNamespace(
            gender="male",
            smoking="no",
            sleep_schedule="early_bird",
            occupation="student",
            area_preference=["Mirpur"],
            budget_max=4500,  # Below 5000
        )
        _, breakdown = CompatibilityEngine.evaluate(budget_tight_seeker, base_listing)
        assert breakdown["budget"] is False

        budget_tight_seeker.budget_max = 5000
        _, breakdown_exact = CompatibilityEngine.evaluate(
            budget_tight_seeker, base_listing
        )
        assert breakdown_exact["budget"] is True

    def test_evaluate_none_profile_returns_zero(self, base_listing: Listing) -> None:
        """None seeker profile safely returns 0 score and empty dict."""
        score, breakdown = CompatibilityEngine.evaluate(None, base_listing)
        assert score == 0
        assert breakdown == {}
