"""Domain models for Tenant Passports and Lifestyle Profiles."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.passports.validators import (
    validate_budget_range,
    validate_dhaka_sub_areas,
    validate_passport_display_name,
)


class Passport(models.Model):
    """Tenant Passport aggregate root proving identity verification."""

    class Status(models.TextChoices):
        UNVERIFIED = "unverified", _("Unverified")
        PENDING = "pending", _("Pending Verification")
        VERIFIED = "verified", _("Verified")
        REJECTED = "rejected", _("Rejected")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="passport",
    )
    display_name = models.CharField(
        max_length=32,
        unique=True,
        validators=[validate_passport_display_name],
        help_text=_("Public handle shown to other tenants (3-32 characters)."),
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.UNVERIFIED,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tenant passport")
        verbose_name_plural = _("Tenant passports")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.get_status_display()})"

    @property
    def is_verified(self) -> bool:
        """Helper checking if passport is in verified state."""
        return self.status == self.Status.VERIFIED

    def clean(self) -> None:
        """Model validation."""
        super().clean()
        if self.display_name:
            self.display_name = self.display_name.strip()
            validate_passport_display_name(self.display_name)


class LifestyleProfile(models.Model):
    """Six-axis lifestyle preferences entity (1:1 with Passport)."""

    class Gender(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")
        OTHER = "other", _("Other")

    class Occupation(models.TextChoices):
        STUDENT = "student", _("Student")
        GARMENTS_WORKER = "garments_worker", _("Garments Worker")
        PRIVATE_JOB = "private_job", _("Private Job")
        FREELANCER = "freelancer", _("Freelancer")
        OTHER = "other", _("Other")

    class Smoking(models.TextChoices):
        YES = "yes", _("Yes")
        NO = "no", _("No")
        OCCASIONALLY = "occasionally", _("Occasionally")

    class SleepSchedule(models.TextChoices):
        EARLY_BIRD = "early_bird", _("Early Bird")
        NIGHT_OWL = "night_owl", _("Night Owl")
        FLEXIBLE = "flexible", _("Flexible")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    passport = models.OneToOneField(
        Passport,
        on_delete=models.CASCADE,
        related_name="lifestyle_profile",
    )
    gender = models.CharField(max_length=16, choices=Gender.choices)
    occupation = models.CharField(max_length=32, choices=Occupation.choices)
    smoking = models.CharField(max_length=16, choices=Smoking.choices)
    sleep_schedule = models.CharField(max_length=16, choices=SleepSchedule.choices)
    area_preference = models.JSONField(
        default=list,
        validators=[validate_dhaka_sub_areas],
        help_text=_("List of preferred Dhaka sub-areas from the canonical 13."),
    )
    budget_min = models.PositiveIntegerField(
        help_text=_("Minimum monthly budget in BDT (৳500+).")
    )
    budget_max = models.PositiveIntegerField(
        help_text=_("Maximum monthly budget in BDT (up to ৳50,000).")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Lifestyle profile")
        verbose_name_plural = _("Lifestyle profiles")

    def __str__(self) -> str:
        return f"Lifestyle for {self.passport.display_name}"

    def clean(self) -> None:
        """Validate bounds and immutability invariants."""
        super().clean()
        if self.budget_min is not None and self.budget_max is not None:
            validate_budget_range(self.budget_min, self.budget_max)
        if self.area_preference is not None:
            validate_dhaka_sub_areas(self.area_preference)

        # Immutability invariant (FR-3): Once verified,
        # lifestyle profile cannot be edited
        if self.pk:
            current = LifestyleProfile.objects.filter(pk=self.pk).first()
            if current and current.passport.is_verified:
                raise ValidationError(
                    _(
                        "Lifestyle profile is immutable once passport is verified. "
                        "A new verification submission is required to update details."
                    )
                )
