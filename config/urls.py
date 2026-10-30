"""Root URL configuration for Basha Pass.

Integrates admin and public URLs allow-list.
"""

from django.contrib import admin
from django.urls import include, path

from apps.passports.views import DashboardView
from config.urls_public import public_urlpatterns

urlpatterns = [
    path("", include("apps.verification.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("passports/", include("apps.passports.urls")),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", include(public_urlpatterns)),
]
