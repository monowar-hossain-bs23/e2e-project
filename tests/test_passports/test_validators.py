"""Unit tests for passport validators and canonical constraints."""

import pytest
from django.core.exceptions import ValidationError

from apps.passports.validators import (
    DHAKA_SUB_AREAS,
    MAX_BUDGET_BDT,
    MIN_BUDGET_BDT,
    validate_budget_range,
    validate_dhaka_sub_areas,
    validate_passport_display_name,
)


class TestPassportDisplayNameValidator:
    """Test display name validation rules (3-32 chars, regex whitelist)."""

    @pytest.mark.parametrize(
        "valid_name",
        [
            "Rahim Ahmed",
            "tanvir_99",
            "Dr. A. K. Azad",
            "Sadia-Khan",
            "O'Connor",
            "Alice 123",
            "abc",
            "a" * 32,
        ],
    )
    def test_valid_display_names(self, valid_name: str) -> None:
        # Should not raise ValidationError
        validate_passport_display_name(valid_name)

    @pytest.mark.parametrize(
        "short_name",
        [
            "",
            "a",
            "ab",
            "  ab  ",
        ],
    )
    def test_display_name_too_short(self, short_name: str) -> None:
        with pytest.raises(ValidationError, match="between 3 and 32 characters"):
            validate_passport_display_name(short_name)

    def test_display_name_too_long(self) -> None:
        too_long = "a" * 33
        with pytest.raises(ValidationError, match="between 3 and 32 characters"):
            validate_passport_display_name(too_long)

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "user@example",
            "name#tag",
            "hacker<script>",
            "name$dollar",
            "emojis 😊",
        ],
    )
    def test_display_name_illegal_characters(self, invalid_name: str) -> None:
        with pytest.raises(ValidationError, match="only contain alphanumeric"):
            validate_passport_display_name(invalid_name)


class TestDhakaSubAreasValidator:
    """Test canonical 13 Dhaka areas validation."""

    def test_canonical_list_contains_13_areas(self) -> None:
        assert len(DHAKA_SUB_AREAS) == 13
        assert "Mirpur" in DHAKA_SUB_AREAS
        assert "Dhanmondi" in DHAKA_SUB_AREAS
        assert "Other" in DHAKA_SUB_AREAS

    def test_valid_subset_passes(self) -> None:
        validate_dhaka_sub_areas(["Mirpur", "Uttara", "Dhanmondi"])

    def test_single_valid_area_passes(self) -> None:
        validate_dhaka_sub_areas(["Gulshan"])

    def test_empty_selection_raises_error(self) -> None:
        with pytest.raises(ValidationError, match="At least one Dhaka area preference"):
            validate_dhaka_sub_areas([])

    def test_invalid_area_raises_error(self) -> None:
        with pytest.raises(ValidationError, match="Invalid Dhaka area"):
            validate_dhaka_sub_areas(["Mirpur", "Sylhet", "Chattogram"])


class TestBudgetRangeValidator:
    """Test budget bounds (৳500 to ৳50,000) and ordering."""

    def test_valid_budget_range(self) -> None:
        validate_budget_range(MIN_BUDGET_BDT, MAX_BUDGET_BDT)
        validate_budget_range(5000, 15000)
        validate_budget_range(10000, 10000)

    def test_budget_below_minimum_raises_error(self) -> None:
        with pytest.raises(ValidationError, match="Minimum budget cannot be less than"):
            validate_budget_range(499, 10000)

    def test_budget_above_maximum_raises_error(self) -> None:
        with pytest.raises(ValidationError, match="Maximum budget cannot exceed"):
            validate_budget_range(5000, 50001)

    def test_min_greater_than_max_raises_error(self) -> None:
        with pytest.raises(
            ValidationError,
            match="Minimum budget cannot be greater than maximum budget",
        ):
            validate_budget_range(12000, 8000)
