"""Tests for project scaffolding and settings configuration."""

from django.conf import settings
from django.core.management import call_command
from django.urls import reverse


def test_django_system_check() -> None:
    """Verifies that Django system check runs without errors or warnings."""
    call_command("check")


def test_settings_configuration() -> None:
    """Verifies key Django configuration variables and directory setups."""
    assert "django.contrib.admin" in settings.INSTALLED_APPS
    assert "django.contrib.auth" in settings.INSTALLED_APPS
    assert settings.ROOT_URLCONF == "config.urls"
    assert settings.TIME_ZONE == "Asia/Dhaka"
    assert settings.MEDIA_PRIVATE_ROOT.exists()
    assert settings.MEDIA_PUBLIC_ROOT.exists()


def test_admin_url_resolves() -> None:
    """Verifies that admin login URL is wired and resolvable."""
    admin_login_url = reverse("admin:login")
    assert admin_login_url == "/admin/login/"
