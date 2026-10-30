"""Tests for User and EmailVerificationToken models."""

import uuid
from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models import EmailVerificationToken, User


@pytest.mark.django_db
class TestUserModel:
    """Test suite for custom User model and manager."""

    def test_create_user_successful(self):
        """Verify normal user creation with default flags and normalized email."""
        user = User.objects.create_user(
            email="  Rimon.Hasan@Example.COM  ",
            password="StrongPassword123!",
            display_name="Rimon",
        )
        assert isinstance(user.id, uuid.UUID)
        assert user.email == "rimon.hasan@example.com"
        assert user.display_name == "Rimon"
        assert user.email_verified is False
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.is_active is True
        assert user.check_password("StrongPassword123!")
        assert str(user) == "Rimon <rimon.hasan@example.com>"

    def test_create_user_missing_email_raises_value_error(self):
        """Verify missing email raises ValueError."""
        with pytest.raises(ValueError, match="The Email field must be set."):
            User.objects.create_user(
                email="",
                password="StrongPassword123!",
                display_name="Rimon",
            )

    def test_create_user_missing_display_name_raises_value_error(self):
        """Verify missing display name raises ValueError."""
        with pytest.raises(ValueError, match="The Display Name field must be set."):
            User.objects.create_user(
                email="rimon@example.com",
                password="StrongPassword123!",
                display_name="",
            )

    def test_create_superuser_successful(self):
        """Verify superuser creation with elevated privileges."""
        admin = User.objects.create_superuser(
            email="admin@bashapass.com",
            password="AdminPassword123!",
            display_name="Founder",
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.email_verified is True
        assert admin.is_active is True

    def test_create_superuser_invalid_staff_flag(self):
        """Verify superuser requires is_staff=True."""
        with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
            User.objects.create_superuser(
                email="admin@bashapass.com",
                password="AdminPassword123!",
                is_staff=False,
            )

    def test_create_superuser_invalid_superuser_flag(self):
        """Verify superuser requires is_superuser=True."""
        with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
            User.objects.create_superuser(
                email="admin@bashapass.com",
                password="AdminPassword123!",
                is_superuser=False,
            )

    def test_unique_email_constraint(self):
        """Verify duplicate email insertion violates uniqueness constraint."""
        User.objects.create_user(
            email="duplicate@example.com",
            password="Password123!",
            display_name="First",
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="duplicate@example.com",
                password="Password456!",
                display_name="Second",
            )

    def test_natural_key_case_insensitive_lookup(self):
        """Verify get_by_natural_key works regardless of case."""
        User.objects.create_user(
            email="rimon@example.com",
            password="Password123!",
            display_name="Rimon",
        )
        found = User.objects.get_by_natural_key("RIMON@EXAMPLE.COM")
        assert found.email == "rimon@example.com"


@pytest.mark.django_db
class TestEmailVerificationTokenModel:
    """Test suite for EmailVerificationToken model."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            email="tokenuser@example.com",
            password="Password123!",
            display_name="TokenUser",
        )

    def test_token_creation_and_properties(self, user):
        """Verify token attributes and valid status."""
        now = timezone.now()
        token = EmailVerificationToken.objects.create(
            user=user,
            token_hash="fakehash123",
            expires_at=now + timedelta(minutes=5),
            resend_count=0,
        )
        assert isinstance(token.id, uuid.UUID)
        assert token.is_valid is True
        assert token.is_expired is False
        assert token.is_consumed is False
        assert "Token(tokenuser@example.com, status=active" in str(token)

    def test_expired_token_property(self, user):
        """Verify is_expired returns True when expires_at has passed."""
        now = timezone.now()
        token = EmailVerificationToken.objects.create(
            user=user,
            token_hash="fakehash123",
            expires_at=now - timedelta(seconds=1),
        )
        assert token.is_expired is True
        assert token.is_valid is False
        assert "status=expired" in str(token)

    def test_consumed_token_property(self, user):
        """Verify is_consumed returns True when consumed_at is set."""
        now = timezone.now()
        token = EmailVerificationToken.objects.create(
            user=user,
            token_hash="fakehash123",
            expires_at=now + timedelta(minutes=5),
            consumed_at=now,
        )
        assert token.is_consumed is True
        assert token.is_valid is False
        assert "status=consumed" in str(token)
