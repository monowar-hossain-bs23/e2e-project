"""Domain models for Accommodation Listings and Listing Photos (PRD §4.4, ERD §4)."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.listings.constants import (
    MAX_BODY_LENGTH,
    ListingKind,
    PreferredGender,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentPeriod,
    RentUnit,
)
from apps.listings.validators import (
    validate_kind_and_rent_unit,
    validate_listing_body,
    validate_pref_occupations,
    validate_rent_bounds,
    validate_single_dhaka_sub_area,
)
from apps.passports.validators import DHAKA_SUB_AREAS


class Listing(models.Model):
    """Aggregate root representing a supply-side room or mess seat post."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        "passports.Passport",
        on_delete=models.RESTRICT,
        related_name="listings",
        help_text=_("Passport of the verified author."),
    )
    kind = models.CharField(
        max_length=8,
        choices=ListingKind.choices,
        db_index=True,
        help_text=_("Accommodation kind: seat in a room or private room."),
    )
    rent_bdt = models.PositiveIntegerField(
        validators=[validate_rent_bounds],
        help_text=_("Monthly rent amount in BDT (৳500–৳50,000)."),
    )
    rent_unit = models.CharField(
        max_length=16,
        choices=RentUnit.choices,
        help_text=_("Rent unit (must match accommodation kind)."),
    )
    rent_period = models.CharField(
        max_length=16,
        choices=RentPeriod.choices,
        default=RentPeriod.PER_MONTH,
        help_text=_("Billing cycle, fixed to per_month in v1."),
    )
    area = models.CharField(
        max_length=64,
        choices=[(a, a) for a in DHAKA_SUB_AREAS],
        validators=[validate_single_dhaka_sub_area],
        db_index=True,
        help_text=_(
            "Dhaka sub-area from the canonical 13 where the accommodation is located."
        ),
    )
    body = models.TextField(
        max_length=MAX_BODY_LENGTH,
        null=True,
        blank=True,
        validators=[validate_listing_body],
        help_text=_("Optional host note describing space and expectations."),
    )
    pref_gender = models.CharField(
        max_length=16,
        choices=PreferredGender.choices,
        default=PreferredGender.ANY,
        help_text=_("Preferred roommate gender."),
    )
    pref_smoking = models.CharField(
        max_length=16,
        choices=PreferredSmoking.choices,
        default=PreferredSmoking.ANY,
        help_text=_("Preferred roommate smoking habit."),
    )
    pref_sleep = models.CharField(
        max_length=16,
        choices=PreferredSleepSchedule.choices,
        default=PreferredSleepSchedule.FLEXIBLE,
        help_text=_("Preferred roommate sleep schedule."),
    )
    pref_occupation = models.JSONField(
        default=list,
        validators=[validate_pref_occupations],
        help_text=_("Preferred roommate occupations (or any)."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_("Timestamp when listing was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("Timestamp when listing was last updated."),
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Timestamp when auto-archived after 60 days."),
    )
    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Timestamp when manually withdrawn by author."),
    )

    class Meta:
        verbose_name = _("Accommodation listing")
        verbose_name_plural = _("Accommodation listings")
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["author", "archived_at", "withdrawn_at"],
                name="listing_author_active_idx",
            ),
            models.Index(
                fields=["-created_at"],
                name="listing_feed_recency_idx",
            ),
        ]

    def __str__(self) -> str:
        area_display = self.area or "Dhaka"
        unit_label = self.get_rent_unit_display()
        kind_label = self.get_kind_display()
        return f"{kind_label} in {area_display} — ৳{self.rent_bdt:,}/{unit_label}"

    @property
    def is_active(self) -> bool:
        """Helper checking if listing is currently active."""
        return self.archived_at is None and self.withdrawn_at is None

    @property
    def is_withdrawn(self) -> bool:
        """Helper checking if listing was manually withdrawn."""
        return self.withdrawn_at is not None

    @property
    def is_archived(self) -> bool:
        """Helper checking if listing was auto-archived."""
        return self.archived_at is not None

    @property
    def status_label(self) -> str:
        """Human-readable lifecycle status label."""
        if self.is_withdrawn:
            return _("Withdrawn")
        if self.is_archived:
            return _("Archived")
        return _("Active")

    @property
    def primary_photo(self) -> "ListingPhoto | None":
        """Return the primary photo based on order."""
        if (
            hasattr(self, "_prefetched_objects_cache")
            and "photos" in self._prefetched_objects_cache
        ):
            photos = list(self.photos.all())
            return photos[0] if photos else None
        return self.photos.order_by("order", "created_at").first()

    def clean(self) -> None:
        """Enforce domain invariants at the model layer."""
        super().clean()
        if self.kind and self.rent_unit:
            validate_kind_and_rent_unit(self.kind, self.rent_unit)


class ListingPhoto(models.Model):
    """Child entity representing an uploaded photo of an accommodation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="photos",
        help_text=_("Associated accommodation listing."),
    )
    photo_path = models.CharField(
        max_length=255,
        help_text=_("Relative path inside media/ directory."),
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("Display order sequence (0 is primary)."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Listing photo")
        verbose_name_plural = _("Listing photos")
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return f"Photo {self.order} for Listing {self.listing_id}"
