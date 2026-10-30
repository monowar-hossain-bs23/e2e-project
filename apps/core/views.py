"""Core public views for Basha Pass."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def landing_view(request: HttpRequest) -> HttpResponse:
    """Public landing page view (per Architecture Spine AD-8).

    Renders the public introduction to Basha Pass with hero value proposition,
    Tenant Passport preview, how-it-works workflow, and social proof.
    """
    context = {
        "verified_listers_count": 142,
        "sub_areas_count": 13,
        "min_rent_bdt": 500,
        "turnaround_hours": 24,
    }
    return render(request, "basha/landing.html", context)
