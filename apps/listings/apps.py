"""Listings application configuration."""

from django.apps import AppConfig


class ListingsConfig(AppConfig):
    """Configuration for Listings app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.listings"
    verbose_name = "Accommodation Listings"
