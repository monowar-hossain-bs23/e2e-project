"""Projection models and value objects for Listing discovery (PRD §4.4, AD-3, AD-12)."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PhotoProjection:
    """Read-model projection of a single listing photo."""

    id: UUID
    url: str
    order: int


@dataclass(frozen=True)
class ListingProjection:
    """Immutable, viewer-scoped projection of an accommodation listing.

    Shields sensitive lister contact PII when viewed by unverified or anonymous
    visitors in strict compliance with Architecture Spine AD-3.
    """

    id: UUID
    kind: str
    kind_display: str
    rent_bdt: int
    rent_unit: str
    rent_unit_display: str
    rent_period: str
    area: str
    body: str | None
    primary_photo_url: str | None
    photos: tuple[PhotoProjection, ...] = field(default_factory=tuple)

    # Author metadata (public handle and tenure)
    author_id: UUID | None = None
    author_display_name: str = ""
    author_tenure_display: str = ""
    author_is_verified: bool = False
    author_lifestyle_summary: str = ""
    author_lifestyle_chips: tuple[str, ...] = field(default_factory=tuple)

    # Roommate lifestyle preferences specified by host
    pref_gender: str = "any"
    pref_gender_display: str = "Any"
    pref_smoking: str = "any"
    pref_smoking_display: str = "Any"
    pref_sleep: str = "flexible"
    pref_sleep_display: str = "Flexible"
    pref_occupations: tuple[str, ...] = field(default_factory=tuple)

    # Soft-gated contact fields (AD-3, PRD §4.5)
    lister_email: str | None = None
    lister_phone: str | None = None
    is_contact_locked: bool = True

    # Lifestyle compatibility matching (AD-12)
    compatibility_hint: int | None = None  # Integer 0 to 6
    compatibility_matches: dict[str, bool] | None = None

    created_at: datetime | None = None
    is_active: bool = True
