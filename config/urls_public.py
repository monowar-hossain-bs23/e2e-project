"""Public URLs allow-list (per Architecture Spine AD-8).

Contains all URLs accessible without authentication.
"""

from django.urls import path
from django.urls.resolvers import URLPattern

from apps.core.views import landing_view

# Canonical list of URL pattern names accessible to unauthenticated visitors
PUBLIC_URL_NAMES: set[str] = {
    "landing",
    "signup",
    "verify_email",
    "resend_otp",
    "login",
    "password_reset",
    "password_reset_done",
    "password_reset_confirm",
    "password_reset_complete",
}

public_urlpatterns: list[URLPattern] = [
    path("", landing_view, name="landing"),
]
