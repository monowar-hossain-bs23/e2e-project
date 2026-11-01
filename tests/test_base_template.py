"""Tests for base template, brand design tokens, and navbar component."""

import pytest
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import RequestFactory

from apps.passports.models import Passport

User = get_user_model()


def test_base_template_renders() -> None:
    """Verifies that templates/base.html renders without template syntax errors."""
    rendered = render_to_string("base.html", {})
    assert "<!doctype html>" in rendered
    assert "Basha Pass" in rendered
    assert "bootstrap@5.3.3" in rendered
    assert "bootstrap-icons" in rendered
    assert "brand-tokens.css" in rendered


def test_base_template_blocks() -> None:
    """Verifies that child templates can extend base.html and populate blocks."""
    child_template_str = """
    {% extends "base.html" %}
    {% block title %}Custom Title{% endblock %}
    {% block content %}
    <main><p>Custom Content Body</p></main>
    {% endblock %}
    """
    template = Template(child_template_str)
    rendered = template.render(Context({}))

    assert "<title>Custom Title</title>" in rendered
    assert "<main><p>Custom Content Body</p></main>" in rendered


@pytest.mark.django_db
class TestNavbarComponent:
    """Tests for the brand navbar across user authentication and verification states."""

    @pytest.fixture
    def request_factory(self) -> RequestFactory:
        return RequestFactory()

    def test_navbar_anonymous_visitor(self, request_factory: RequestFactory) -> None:
        request = request_factory.get("/")
        # AnonymousUser mock
        from django.contrib.auth.models import AnonymousUser

        request.user = AnonymousUser()

        rendered = render_to_string("basha/partials/navbar.html", request=request)
        assert "bp-brand" in rendered
        assert "bp-brand__mark" in rendered
        assert "How it works" in rendered
        assert "Log in" in rendered
        assert "Create account" in rendered
        assert "Dashboard" not in rendered

    def test_navbar_authenticated_unverified_tenant(
        self, request_factory: RequestFactory
    ) -> None:
        user = User.objects.create_user(
            email="nav_unverified@example.com",
            password="Password123!",
            display_name="Rimon",
        )
        request = request_factory.get("/")
        request.user = user

        rendered = render_to_string("basha/partials/navbar.html", request=request)
        assert "bp-brand" in rendered
        assert "Dashboard" in rendered
        assert "Verify Passport" in rendered
        assert "bp-avatar" in rendered
        assert "R" in rendered
        assert "Rimon" in rendered
        assert "userMenuDropdown" in rendered
        assert "Account Settings" in rendered
        assert "Log out" in rendered
        assert "bp-verified-pill" not in rendered

    def test_navbar_authenticated_verified_tenant(
        self, request_factory: RequestFactory
    ) -> None:
        user = User.objects.create_user(
            email="nav_verified@example.com",
            password="Password123!",
            display_name="Tanvir",
        )
        Passport.objects.create(
            user=user,
            display_name="Tanvir",
            status=Passport.Status.VERIFIED,
        )
        request = request_factory.get("/")
        request.user = user

        rendered = render_to_string("basha/partials/navbar.html", request=request)
        assert "bp-brand" in rendered
        assert "Dashboard" in rendered
        assert "bp-verified-pill" in rendered
        assert "Verified" in rendered
        assert "Verify Passport" not in rendered
        assert "T" in rendered
        assert "Tanvir" in rendered
        assert "userMenuDropdown" in rendered
        assert "Account Settings" in rendered
