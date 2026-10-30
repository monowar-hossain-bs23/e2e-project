"""URL configuration for Tenant Passports and verification dashboards."""

from django.urls import path

from apps.passports.views import (
    DashboardStatusPartialView,
    PassportWizardView,
)

urlpatterns = [
    path("create/", PassportWizardView.as_view(), name="passport_create"),
    path("wizard/", PassportWizardView.as_view(), name="passport_wizard"),
    path(
        "dashboard/status-partial/",
        DashboardStatusPartialView.as_view(),
        name="dashboard_status_partial",
    ),
]
