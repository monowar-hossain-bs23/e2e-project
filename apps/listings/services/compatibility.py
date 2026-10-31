"""Lifestyle compatibility evaluation engine (PRD §4.4, Architecture Spine AD-12)."""

from typing import Any


class CompatibilityEngine:
    """Evaluates 6-axis lifestyle compatibility between seeker and listing.

    Computes an objective, transparent integer score X in [0, 6] based on:
    1. Gender preference
    2. Smoking habit
    3. Sleep schedule
    4. Occupation
    5. Area preference
    6. Budget range

    Per Architecture Spine AD-12 and PRD §4.4, no percentage, star rating, or
    algorithmic ranking is ever produced or stored.
    """

    @classmethod
    def evaluate(cls, seeker_profile: Any, listing: Any) -> tuple[int, dict[str, bool]]:
        """Evaluate alignment across all 6 lifestyle dimensions.

        Returns:
            tuple of (match_score: int in 0..6, breakdown: dict[str, bool])
        """
        if not seeker_profile:
            return 0, {}

        # 1. Gender alignment
        seeker_gender = getattr(seeker_profile, "gender", None)
        gender_match = bool(
            listing.pref_gender == "any"
            or (seeker_gender and listing.pref_gender == seeker_gender)
        )

        # 2. Smoking alignment
        seeker_smoking = getattr(seeker_profile, "smoking", None)
        smoking_match = bool(
            listing.pref_smoking == "any"
            or (seeker_smoking and listing.pref_smoking == seeker_smoking)
        )

        # 3. Sleep schedule alignment
        seeker_sleep = getattr(seeker_profile, "sleep_schedule", None)
        sleep_match = bool(
            listing.pref_sleep == "flexible"
            or (seeker_sleep and listing.pref_sleep == seeker_sleep)
        )

        # 4. Occupation alignment
        occ_list = listing.pref_occupation or []
        seeker_occ = getattr(seeker_profile, "occupation", None)
        occ_match = bool("any" in occ_list or (seeker_occ and seeker_occ in occ_list))

        # 5. Area preference alignment
        seeker_areas = (
            getattr(seeker_profile, "area_preference", None)
            or getattr(seeker_profile, "preferred_areas", None)
            or []
        )
        area_match = bool(listing.area in seeker_areas)

        # 6. Budget alignment (listing rent fits within seeker budget max)
        budget_max = getattr(seeker_profile, "budget_max", None)
        if budget_max is None:
            budget_max = getattr(seeker_profile, "budget_bdt", None)

        budget_match = bool(budget_max is not None and listing.rent_bdt <= budget_max)

        breakdown = {
            "gender": gender_match,
            "smoking": smoking_match,
            "sleep": sleep_match,
            "occupation": occ_match,
            "area": area_match,
            "budget": budget_match,
        }
        score = sum(1 for matched in breakdown.values() if matched)
        return score, breakdown
