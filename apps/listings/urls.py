"""URL routing for accommodation listings authoring and management."""

from django.urls import path

from apps.listings.views import (
    ListerDashboardView,
    ListingCreateView,
    ListingEditView,
    ListingWithdrawView,
)

urlpatterns = [
    path("create/", ListingCreateView.as_view(), name="listing_create"),
    path("mine/", ListerDashboardView.as_view(), name="listing_mine"),
    path("<uuid:pk>/edit/", ListingEditView.as_view(), name="listing_edit"),
    path(
        "<uuid:pk>/withdraw/",
        ListingWithdrawView.as_view(),
        name="listing_withdraw",
    ),
]
