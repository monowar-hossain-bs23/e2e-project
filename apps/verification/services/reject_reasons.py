"""Canonical verification rejection reason codes enum (Architecture Spine AD-4)."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class RejectReason(models.TextChoices):
    """Canonical 5-member reason code enum required for any rejection."""

    EXPIRED = "expired", _("Document Expired")
    MISMATCH = "mismatch", _("Information Mismatch")
    ILLEGIBLE = "illegible", _("Illegible Image")
    TAMPERING_SUSPECTED = "tampering_suspected", _("Tampering Suspected")
    OTHER = "other", _("Other")
