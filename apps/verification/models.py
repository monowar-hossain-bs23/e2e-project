"""Domain models for Verification attempts and review tracking."""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.verification.services.reject_reasons import RejectReason


class Verification(models.Model):
    """A discrete verification attempt for a Tenant Passport."""

    class State(models.TextChoices):
        SUBMITTED = "submitted", _("Submitted")
        REVIEWING = "reviewing", _("Reviewing")
        VERIFIED = "verified", _("Verified")
        REJECTED = "rejected", _("Rejected")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passport = models.ForeignKey(
        "passports.Passport",
        on_delete=models.CASCADE,
        related_name="verifications",
    )
    state = models.CharField(
        max_length=16,
        choices=State.choices,
        default=State.SUBMITTED,
        db_index=True,
    )
    nid_front_path = models.CharField(
        max_length=255,
        help_text=_("Relative path inside media_private/ to NID front image."),
    )
    nid_back_path = models.CharField(
        max_length=255,
        help_text=_("Relative path inside media_private/ to NID back image."),
    )
    selfie_path = models.CharField(
        max_length=255,
        help_text=_("Relative path inside media_private/ to selfie holding NID."),
    )
    reject_reason = models.CharField(
        max_length=32,
        choices=RejectReason.choices,
        null=True,
        blank=True,
        help_text=_("Canonical reason code required if rejected."),
    )
    reviewer_notes = models.TextField(
        null=True,
        blank=True,
        help_text=_("Internal staff notes explaining review decision."),
    )
    submitted_at = models.DateTimeField(
        db_index=True,
        help_text=_("Timestamp when user submitted for FIFO queue sorting."),
    )
    last_rejection_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp of rejection used for 24-hour cooldown enforcement."),
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_verifications",
        help_text=_("Staff member who evaluated this submission."),
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp when staff finalized review decision."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Verification attempt")
        verbose_name_plural = _("Verification attempts")
        ordering = ["submitted_at"]  # Strict FIFO queue per FR-7

    def __str__(self) -> str:
        name = self.passport.display_name
        return f"Verification for {name} [{self.get_state_display()}]"
