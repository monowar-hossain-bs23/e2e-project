"""Integration tests for the Basha Pass landing page."""

from django.test import Client
from django.urls import reverse


def test_landing_url_reverse() -> None:
    """Verifies that reverse('landing') resolves to root path '/'."""
    assert reverse("landing") == "/"


def test_landing_page_status_code(client: Client) -> None:
    """Verifies that accessing root '/' returns HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_landing_page_template_used(client: Client) -> None:
    """Verifies that basha/landing.html and its partials are rendered."""
    response = client.get("/")
    assert response.status_code == 200
    templates_used = [t.name for t in response.templates if t.name]
    assert "basha/landing.html" in templates_used
    assert "base.html" in templates_used
    assert "basha/partials/navbar.html" in templates_used
    assert "basha/partials/passport_preview.html" in templates_used
    assert "basha/partials/how_it_works.html" in templates_used
    assert "basha/partials/testimonials.html" in templates_used
    assert "basha/partials/cta_banner.html" in templates_used
    assert "basha/partials/footer.html" in templates_used


def test_landing_page_content(client: Client) -> None:
    """Verifies key copy, branding, and value propositions are rendered."""
    response = client.get("/")
    content = response.content.decode("utf-8")

    # Brand and header
    assert "Basha Pass" in content
    assert "Find a verified roommate in Dhaka" in content

    # Value propositions and trust
    assert "without handing your NID to strangers" in content
    assert "NID verified by police portal" in content
    assert "Reviewed in ~24 hours" in content

    # Preview card
    assert "Rimon H." in content
    assert "Mirpur · verified 4 months" in content
    assert "Matches 5 of 6" in content

    # 3-step workflow
    assert "Three steps. No group posts, no NID handoffs." in content
    assert "Verify your passport" in content
    assert "Browse verified seats &amp; rooms" in content
    assert "Reach out off-platform" in content

    # Stats strip
    assert "Minimum rent tracked" in content
    assert "Dhaka sub-areas" in content

    # Footer
    assert "&copy; 2026 Basha Pass · Dhaka" in content
