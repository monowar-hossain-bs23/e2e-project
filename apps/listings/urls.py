"""URL routing for accommodation listings discovery, authoring, and management."""

from django.urls import path

from apps.listings.views import (
    ListerDashboardView,
    ListingCreateView,
    ListingDetailView,
    ListingEditView,
    ListingFeedView,
    ListingWithdrawView,
)

urlpatterns = [
    path("", ListingFeedView.as_view(), name="listing_feed"),
    path("create/", ListingCreateView.as_view(), name="listing_create"),
    path("mine/", ListerDashboardView.as_view(), name="listing_mine"),
    path("<uuid:pk>/", ListingDetailView.as_view(), name="listing_detail"),
    path("<uuid:pk>/edit/", ListingEditView.as_view(), name="listing_edit"),
    path(
        "<uuid:pk>/withdraw/",
        ListingWithdrawView.as_view(),
        name="listing_withdraw",
    ),
]
