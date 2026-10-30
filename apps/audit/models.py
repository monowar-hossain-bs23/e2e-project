"""Audit models for immutable compliance and operational history (AD-15)."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditEntry(models.Model):
    """Append-only audit trail record capturing state mutations across services."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_id = models.UUIDField(
        db_index=True,
        help_text=_("UUID of the user who initiated the action."),
    )
    target_type = models.CharField(
        max_length=64,
        db_index=True,
        help_text=_(
            "Polymorphic string type of the target (e.g. 'verification.Verification')."
        ),
    )
    target_id = models.UUIDField(
        db_index=True,
        help_text=_("Primary key UUID of the target entity."),
    )
    action = models.CharField(
        max_length=32,
        help_text=_("Action verb, e.g. 'transition', 'create', 'update'."),
    )
    before_state = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Snapshot dictionary prior to state change."),
    )
    after_state = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Snapshot dictionary after state change."),
    )
    reason_code = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text=_("Canonical reason enum value if applicable."),
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_("UTC timestamp when the action occurred."),
    )

    class Meta:
        verbose_name = _("Audit entry")
        verbose_name_plural = _("Audit entries")
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M")
        return f"[{ts}] {self.action} on {self.target_type} by {self.actor_id}"

    def save(self, *args, **kwargs) -> None:
        """Enforce append-only constraint."""
        if self.pk and AuditEntry.objects.filter(pk=self.pk).exists():
            raise ValidationError(
                _("AuditEntry rows are append-only and cannot be updated.")
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of audit entries."""
        raise ValidationError(_("AuditEntry rows are immutable and cannot be deleted."))
