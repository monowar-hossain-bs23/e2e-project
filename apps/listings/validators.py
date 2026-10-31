"""Validators for Listing domain invariants and inputs."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.listings.constants import (
    MAX_BODY_LENGTH,
    MAX_RENT_BDT,
    MIN_RENT_BDT,
    ListingKind,
    PreferredOccupation,
    RentUnit,
)
from apps.passports.validators import validate_dhaka_sub_areas

__all__ = [
    "validate_dhaka_sub_areas",
    "validate_rent_bounds",
    "validate_kind_and_rent_unit",
    "validate_pref_occupations",
    "validate_listing_body",
]


def validate_rent_bounds(value: int) -> None:
    """Validate that monthly rent is between ৳500 and ৳50,000 BDT."""
    if value < MIN_RENT_BDT or value > MAX_RENT_BDT:
        raise ValidationError(
            _(
                f"Rent must be between ৳{MIN_RENT_BDT:,} and "
                f"৳{MAX_RENT_BDT:,} BDT per month."
            )
        )


def validate_kind_and_rent_unit(kind: str, rent_unit: str) -> None:
    """Validate cross-field consistency between kind and rent_unit (AD-6)."""
    if kind == ListingKind.SEAT and rent_unit != RentUnit.PER_SEAT:
        raise ValidationError(
            _("A seat listing must have rent unit set to 'per_seat'.")
        )
    if kind == ListingKind.ROOM and rent_unit != RentUnit.PER_ROOM:
        raise ValidationError(
            _("A room listing must have rent unit set to 'per_room'.")
        )


def validate_pref_occupations(occupations: list[str]) -> None:
    """Validate that preferred occupations belong to canonical occupation choices."""
    if not isinstance(occupations, list):
        raise ValidationError(_("Preferred occupations must be provided as a list."))
    valid_choices = set(PreferredOccupation.values)
    invalid = [occ for occ in occupations if occ not in valid_choices]
    if invalid:
        raise ValidationError(
            _(f"Invalid occupation choice(s) specified: {', '.join(invalid)}.")
        )


def validate_listing_body(value: str | None) -> None:
    """Validate optional listing body note length."""
    if value and len(value) > MAX_BODY_LENGTH:
        raise ValidationError(
            _(f"Listing notes cannot exceed {MAX_BODY_LENGTH} characters.")
        )
