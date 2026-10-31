"""ListingService: Sole mutator governing accommodation listing lifecycle (AD-6)."""

import logging
from datetime import timedelta
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.audit.services.audit_service import AuditService
from apps.listings.constants import (
    AUTO_ARCHIVE_DAYS,
    MAX_ACTIVE_LISTINGS_PER_USER,
    MAX_LISTING_PHOTOS,
    MIN_LISTING_PHOTOS,
    PreferredGender,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentPeriod,
)
from apps.listings.models import Listing, ListingPhoto
from apps.listings.services.storage import ListingPhotoStorageService
from apps.listings.validators import (
    validate_kind_and_rent_unit,
    validate_listing_body,
    validate_pref_occupations,
    validate_rent_bounds,
    validate_single_dhaka_sub_area,
)
from apps.passports.models import Passport

logger = logging.getLogger(__name__)


class ListingService:
    """Sole mutator governing listing creation, invariants, cap, and lifecycle."""

    @classmethod
    def check_active_cap(cls, passport: Passport) -> int:
        """Return the count of currently active listings for a tenant."""
        return Listing.objects.filter(
            author=passport,
            archived_at__isnull=True,
            withdrawn_at__isnull=True,
        ).count()

    @classmethod
    def create(
        cls,
        author: Passport,
        *,
        kind: str,
        rent_bdt: int,
        rent_unit: str,
        area: str,
        body: str | None = None,
        pref_gender: str = PreferredGender.ANY,
        pref_smoking: str = PreferredSmoking.ANY,
        pref_sleep: str = PreferredSleepSchedule.FLEXIBLE,
        pref_occupation: list[str] | None = None,
        photo_files: list[Any],
    ) -> dict[str, Any]:
        """Create a new listing enforcing verified author, active cap, invariants."""
        if not getattr(author, "is_verified", False):
            return {
                "ok": False,
                "code": "unverified_author",
                "message": _(
                    "Only verified tenants can create accommodation listings. "
                    "Please complete your Tenant Passport verification first."
                ),
            }

        # Validate inputs
        try:
            validate_kind_and_rent_unit(kind, rent_unit)
            validate_rent_bounds(rent_bdt)
            validate_single_dhaka_sub_area(area)
            validate_listing_body(body)
            if pref_occupation:
                validate_pref_occupations(pref_occupation)
            ListingPhotoStorageService.validate_photo_batch(photo_files)
        except ValidationError as exc:
            return {
                "ok": False,
                "code": "invalid_parameters",
                "message": exc.messages[0] if hasattr(exc, "messages") else str(exc),
            }

        clean_occupations = pref_occupation or []

        with transaction.atomic():
            # Lock author's Passport row to serialize active-cap check
            Passport.objects.select_for_update().get(id=author.id)

            active_count = cls.check_active_cap(author)
            if active_count >= MAX_ACTIVE_LISTINGS_PER_USER:
                return {
                    "ok": False,
                    "code": "active_cap_reached",
                    "message": _(
                        f"You have reached the limit of {MAX_ACTIVE_LISTINGS_PER_USER} "
                        "active listings. Archive or withdraw an existing post."
                    ),
                }

            now = timezone.now()
            listing = Listing.objects.create(
                author=author,
                kind=kind,
                rent_bdt=rent_bdt,
                rent_unit=rent_unit,
                rent_period=RentPeriod.PER_MONTH,
                area=area,
                body=body,
                pref_gender=pref_gender,
                pref_smoking=pref_smoking,
                pref_sleep=pref_sleep,
                pref_occupation=clean_occupations,
            )

            # Persist photos
            for idx, photo_file in enumerate(photo_files):
                rel_path = ListingPhotoStorageService.save_photo(
                    file=photo_file,
                    listing_id=listing.id,
                    order=idx,
                )
                ListingPhoto.objects.create(
                    listing=listing,
                    photo_path=rel_path,
                    order=idx,
                )

            # Audit record
            AuditService.append(
                actor_id=author.user.pk,
                target=listing,
                action="create",
                before_state=None,
                after_state={
                    "kind": kind,
                    "rent_bdt": rent_bdt,
                    "rent_unit": rent_unit,
                    "area": area,
                    "photos_count": len(photo_files),
                    "created_at": now.isoformat(),
                },
            )

        logger.info("Listing %s created by author %s", listing.pk, author.pk)
        return {"ok": True, "listing": listing}

    @classmethod
    def edit(
        cls,
        listing: Listing,
        *,
        actor: Any,
        fields: dict[str, Any],
        new_photo_files: list[Any] | None = None,
        delete_photo_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update mutable fields while protecting locked fields (kind, area)."""
        is_owner = (
            actor == listing.author.user
            or getattr(actor, "is_staff", False)
            or (hasattr(actor, "passport") and actor.passport == listing.author)
        )
        if not is_owner:
            return {
                "ok": False,
                "code": "forbidden_actor",
                "message": _("You do not have permission to edit this listing."),
            }

        # Check for attempted modification of locked fields
        if "kind" in fields or "area" in fields:
            return {
                "ok": False,
                "code": "field_locked",
                "message": _(
                    "Accommodation kind and area are permanent "
                    "and cannot be modified once published."
                ),
            }

        # Validate mutable fields
        updated_rent = fields.get("rent_bdt", listing.rent_bdt)
        updated_rent_unit = fields.get("rent_unit", listing.rent_unit)
        updated_body = fields.get("body", listing.body)
        updated_gender = fields.get("pref_gender", listing.pref_gender)
        updated_smoking = fields.get("pref_smoking", listing.pref_smoking)
        updated_sleep = fields.get("pref_sleep", listing.pref_sleep)
        updated_occupation = fields.get("pref_occupation", listing.pref_occupation)

        try:
            validate_kind_and_rent_unit(listing.kind, updated_rent_unit)
            validate_rent_bounds(updated_rent)
            validate_listing_body(updated_body)
            if updated_occupation:
                validate_pref_occupations(updated_occupation)
        except ValidationError as exc:
            return {
                "ok": False,
                "code": "invalid_parameters",
                "message": exc.messages[0] if hasattr(exc, "messages") else str(exc),
            }

        # Validate photos
        new_photos = new_photo_files or []
        delete_ids = set(str(pid) for pid in (delete_photo_ids or []))
        current_photos = list(listing.photos.all())
        photos_to_keep = [p for p in current_photos if str(p.id) not in delete_ids]
        projected_count = len(photos_to_keep) + len(new_photos)

        if projected_count < MIN_LISTING_PHOTOS:
            return {
                "ok": False,
                "code": "invalid_photo_count",
                "message": _(
                    f"A listing must retain at least {MIN_LISTING_PHOTOS} photo."
                ),
            }
        if projected_count > MAX_LISTING_PHOTOS:
            return {
                "ok": False,
                "code": "invalid_photo_count",
                "message": _(f"A listing cannot exceed {MAX_LISTING_PHOTOS} photos."),
            }

        for pfile in new_photos:
            try:
                ListingPhotoStorageService.validate_photo_file(pfile)
            except ValidationError as exc:
                return {
                    "ok": False,
                    "code": "invalid_photo_file",
                    "message": str(exc),
                }

        before_state = {
            "rent_bdt": listing.rent_bdt,
            "rent_unit": listing.rent_unit,
            "body": listing.body,
        }

        with transaction.atomic():
            listing.rent_bdt = updated_rent
            listing.rent_unit = updated_rent_unit
            listing.body = updated_body
            listing.pref_gender = updated_gender
            listing.pref_smoking = updated_smoking
            listing.pref_sleep = updated_sleep
            listing.pref_occupation = updated_occupation or []
            listing.save()

            # Handle photo deletions
            for photo in current_photos:
                if str(photo.id) in delete_ids:
                    ListingPhotoStorageService.delete_photo(photo.photo_path)
                    photo.delete()

            # Handle new photo uploads
            current_max_order = (
                listing.photos.aggregate(models.Max("order"))["order__max"] or 0
            )
            for idx, photo_file in enumerate(new_photos):
                order = current_max_order + idx + 1
                rel_path = ListingPhotoStorageService.save_photo(
                    file=photo_file,
                    listing_id=listing.id,
                    order=order,
                )
                ListingPhoto.objects.create(
                    listing=listing,
                    photo_path=rel_path,
                    order=order,
                )

            # Normalize photo ordering starting at 0
            for idx, p in enumerate(listing.photos.order_by("order", "created_at")):
                if p.order != idx:
                    p.order = idx
                    p.save(update_fields=["order"])

            after_state = {
                "rent_bdt": listing.rent_bdt,
                "rent_unit": listing.rent_unit,
                "body": listing.body,
                "photos_count": projected_count,
            }

            AuditService.append(
                actor_id=actor.pk,
                target=listing,
                action="edit",
                before_state=before_state,
                after_state=after_state,
            )

        logger.info("Listing %s edited by actor %s", listing.pk, actor.pk)
        return {"ok": True, "listing": listing}

    @classmethod
    def withdraw(cls, listing: Listing, *, actor: Any) -> dict[str, Any]:
        """Manually withdraw an active listing, removing it from active cap."""
        is_owner = (
            actor == listing.author.user
            or getattr(actor, "is_staff", False)
            or (hasattr(actor, "passport") and actor.passport == listing.author)
        )
        if not is_owner:
            return {
                "ok": False,
                "code": "forbidden_actor",
                "message": _("You do not have permission to withdraw this listing."),
            }

        if listing.is_withdrawn:
            return {"ok": True, "listing": listing, "message": "Already withdrawn."}

        with transaction.atomic():
            before_state = {"withdrawn_at": None}
            now = timezone.now()
            listing.withdrawn_at = now
            listing.save(update_fields=["withdrawn_at", "updated_at"])

            AuditService.append(
                actor_id=actor.pk,
                target=listing,
                action="withdraw",
                before_state=before_state,
                after_state={"withdrawn_at": now.isoformat()},
            )

        logger.info("Listing %s withdrawn by actor %s", listing.pk, actor.pk)
        return {"ok": True, "listing": listing}

    @classmethod
    def archive_stale(cls, cutoff_days: int = AUTO_ARCHIVE_DAYS) -> dict[str, Any]:
        """Auto-archive active listings older than cutoff_days (default 60 days)."""
        cutoff = timezone.now() - timedelta(days=cutoff_days)
        stale_qs = Listing.objects.filter(
            archived_at__isnull=True,
            withdrawn_at__isnull=True,
            created_at__lt=cutoff,
        )

        archived_count = 0
        now = timezone.now()

        for listing in stale_qs:
            with transaction.atomic():
                listing.archived_at = now
                listing.save(update_fields=["archived_at", "updated_at"])

                AuditService.append(
                    actor_id=listing.author.user.pk,
                    target=listing,
                    action="archive_stale",
                    before_state={"archived_at": None},
                    after_state={"archived_at": now.isoformat()},
                    reason_code="60_day_stale_archival",
                )
                archived_count += 1

        logger.info(
            "Archived %d stale listings older than %d days",
            archived_count,
            cutoff_days,
        )
        return {"ok": True, "archived_count": archived_count}
