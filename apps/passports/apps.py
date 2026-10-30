"""Passports application configuration."""

from django.apps import AppConfig


class PassportsConfig(AppConfig):
    """Configuration for Passports app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.passports"
    verbose_name = "Tenant Passports"
