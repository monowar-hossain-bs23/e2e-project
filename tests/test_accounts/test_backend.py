"""Tests for CaseInsensitiveModelBackend."""

import pytest
from django.test import RequestFactory

from apps.accounts.backends import CaseInsensitiveModelBackend
from apps.accounts.models import User


@pytest.mark.django_db
class TestCaseInsensitiveModelBackend:
    """Test suite for case-insensitive email authentication."""

    @pytest.fixture
    def backend(self):
        return CaseInsensitiveModelBackend()

    @pytest.fixture
    def request_factory(self):
        return RequestFactory()

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email="tenant.dhaka@example.com",
            password="StrongPassword123!",
            display_name="TenantDhaka",
        )

    def test_authenticate_with_lowercase_email(self, backend, request_factory, user):
        """Verify authentication works with exact lowercase email."""
        req = request_factory.get("/")
        auth_user = backend.authenticate(
            request=req,
            username="tenant.dhaka@example.com",
            password="StrongPassword123!",
        )
        assert auth_user == user

    def test_authenticate_with_uppercase_email(self, backend, request_factory, user):
        """Verify authentication works with uppercase email input."""
        req = request_factory.get("/")
        auth_user = backend.authenticate(
            request=req,
            username="TENANT.DHAKA@EXAMPLE.COM",
            password="StrongPassword123!",
        )
        assert auth_user == user

    def test_authenticate_with_mixed_case_email(self, backend, request_factory, user):
        """Verify authentication works with mixed-case email input."""
        req = request_factory.get("/")
        auth_user = backend.authenticate(
            request=req,
            email="Tenant.Dhaka@Example.Com",
            password="StrongPassword123!",
        )
        assert auth_user == user

    def test_authenticate_with_wrong_password_fails(
        self, backend, request_factory, user
    ):
        """Verify authentication fails when given wrong password."""
        req = request_factory.get("/")
        auth_user = backend.authenticate(
            request=req,
            username="tenant.dhaka@example.com",
            password="WrongPassword123!",
        )
        assert auth_user is None

    def test_authenticate_nonexistent_user_fails(self, backend, request_factory):
        """Verify authentication fails for non-existent email."""
        req = request_factory.get("/")
        auth_user = backend.authenticate(
            request=req,
            username="nobody@example.com",
            password="SomePassword123!",
        )
        assert auth_user is None

    def test_authenticate_inactive_user_fails(self, backend, request_factory, user):
        """Verify inactive user cannot authenticate."""
        user.is_active = False
        user.save()

        req = request_factory.get("/")
        auth_user = backend.authenticate(
            request=req,
            username="tenant.dhaka@example.com",
            password="StrongPassword123!",
        )
        assert auth_user is None
