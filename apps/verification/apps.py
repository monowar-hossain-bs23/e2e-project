"""Verification application configuration."""

from django.apps import AppConfig


class VerificationConfig(AppConfig):
    """Configuration for Verification app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.verification"
    verbose_name = "Identity Verification"
