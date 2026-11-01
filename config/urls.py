"""Root URL configuration for Basha Pass.

Integrates admin and public URLs allow-list.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from apps.passports.views import DashboardView
from config.urls_public import public_urlpatterns

urlpatterns = [
    path("", include("apps.verification.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("passports/", include("apps.passports.urls")),
    path("listings/", include("apps.listings.urls")),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", include(public_urlpatterns)),
]

if settings.DEBUG or getattr(settings, "TESTING", False):
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
            name="media",
        ),
    ]
