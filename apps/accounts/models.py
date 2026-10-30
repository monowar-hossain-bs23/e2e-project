"""Models for Accounts & Identity context."""

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for Basha Pass tenants and administrative staff."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Standard UUID4 primary key.",
    )
    email = models.EmailField(
        unique=True,
        max_length=254,
        db_index=True,
        help_text="Unique normalized email address.",
    )
    display_name = models.CharField(
        max_length=32,
        help_text="Public-facing handle shown to other tenants (2–32 chars).",
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Designates whether the user has verified their email via OTP.",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into the Django admin site.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this user account should be treated as active.",
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        help_text="Date and time when user registered.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when row was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when row was last updated.",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.display_name} <{self.email}>"

    def clean(self) -> None:
        """Normalize email before validation or save."""
        super().clean()
        if self.email:
            self.email = self.email.strip().lower()

    def save(self, *args, **kwargs) -> None:
        """Ensure clean() is executed on save."""
        self.clean()
        super().save(*args, **kwargs)


class EmailVerificationToken(models.Model):
    """Ephemeral 6-digit OTP verification token for user onboarding."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
    )
    token_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hex digest of the 6-digit verification code.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when token was issued.",
    )
    expires_at = models.DateTimeField(
        help_text="Expiry timestamp (created_at + 5 mins).",
    )
    consumed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when token was verified and consumed.",
    )
    resend_count = models.PositiveSmallIntegerField(
        default=0,
        help_text="Total resend requests issued for this signup session (max 3).",
    )

    class Meta:
        verbose_name = "Email Verification Token"
        verbose_name_plural = "Email Verification Tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        if self.consumed_at:
            status = "consumed"
        elif self.is_expired:
            status = "expired"
        else:
            status = "active"
        return f"Token({self.user.email}, status={status}, resends={self.resend_count})"

    @property
    def is_expired(self) -> bool:
        """Return True if the current time has passed the expiration timestamp."""
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        """Return True if the token has already been consumed."""
        return self.consumed_at is not None

    @property
    def is_valid(self) -> bool:
        """Return True if the token is active, unconsumed, and not expired."""
        return not self.is_consumed and not self.is_expired
