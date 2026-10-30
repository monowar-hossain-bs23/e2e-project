"""Validators and canonical choices for Passports and Lifestyle Profiles."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

DISPLAY_NAME_REGEX = re.compile(r"^[A-Za-z0-9 ._\-']+$")

DHAKA_SUB_AREAS: tuple[str, ...] = (
    "Mirpur",
    "Mohammadpur",
    "Uttara",
    "Banani",
    "Gulshan",
    "Baridhara",
    "Bashundhara",
    "Dhanmondi",
    "Ramna",
    "Tejgaon",
    "Gazipur",
    "Narayanganj-adjacent",
    "Other",
)

MIN_BUDGET_BDT: int = 500
MAX_BUDGET_BDT: int = 50000


def validate_passport_display_name(value: str) -> None:
    """Validate that display name is between 3 and 32 characters and contains

    only permitted characters.
    """
    clean_val = value.strip()
    if len(clean_val) < 3 or len(clean_val) > 32:
        raise ValidationError(
            _("Display name must be between 3 and 32 characters long.")
        )
    if not DISPLAY_NAME_REGEX.match(clean_val):
        raise ValidationError(
            _(
                "Display name may only contain alphanumeric characters, spaces, "
                "and basic punctuation (. _ - ')."
            )
        )


def validate_dhaka_sub_areas(areas: list[str]) -> None:
    """Validate that area preferences are a subset of canonical Dhaka areas."""
    if not areas:
        raise ValidationError(_("At least one Dhaka area preference must be selected."))
    invalid = [area for area in areas if area not in DHAKA_SUB_AREAS]
    if invalid:
        raise ValidationError(
            _(f"Invalid Dhaka area(s) specified: {', '.join(invalid)}.")
        )


def validate_budget_range(budget_min: int, budget_max: int) -> None:
    """Validate budget bounds and ordering."""
    if budget_min < MIN_BUDGET_BDT:
        raise ValidationError(
            _(f"Minimum budget cannot be less than ৳{MIN_BUDGET_BDT}.")
        )
    if budget_max > MAX_BUDGET_BDT:
        raise ValidationError(_(f"Maximum budget cannot exceed ৳{MAX_BUDGET_BDT}."))
    if budget_min > budget_max:
        raise ValidationError(
            _("Minimum budget cannot be greater than maximum budget.")
        )
