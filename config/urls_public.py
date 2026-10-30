"""Public URLs allow-list (per Architecture Spine AD-8).

Contains all URLs accessible without authentication.
"""

from django.urls import path
from django.urls.resolvers import URLPattern

from apps.core.views import landing_view

public_urlpatterns: list[URLPattern] = [
    path("", landing_view, name="landing"),
]
