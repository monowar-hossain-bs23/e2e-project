"""Tests for AccountService business logic and OTP operations."""

from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import EmailVerificationToken, User
from apps.accounts.services.account_service import AccountService


@pytest.mark.django_db
class TestAccountService:
    """Test suite for AccountService."""

    def test_register_user_success(self):
        """Verify successful user registration and OTP email dispatch."""
        res = AccountService.register_user(
            email="newuser@example.com",
            password="StrongPassword123!",
            display_name="NewUser",
        )
        assert res["ok"] is True
        user = res["user"]
        raw_otp = res["raw_otp"]
        assert len(raw_otp) == 6
        assert raw_otp.isdigit()
        assert user.email_verified is False

        # Verify email in outbox
        assert len(mail.outbox) == 1
        email_msg = mail.outbox[0]
        assert email_msg.to == ["newuser@example.com"]
        assert "Your Basha Pass Verification Code" in email_msg.subject
        assert raw_otp in email_msg.body

        # Verify token in DB is hashed
        token = EmailVerificationToken.objects.get(id=res["token_id"])
        assert token.token_hash != raw_otp
        assert len(token.token_hash) == 64
        assert token.resend_count == 0

    def test_register_user_duplicate_email_fails(self):
        """Verify registration with already registered email returns error envelope."""
        User.objects.create_user(
            email="existing@example.com",
            password="Password123!",
            display_name="Existing",
        )
        res = AccountService.register_user(
            email="EXISTING@example.com",
            password="StrongPassword123!",
            display_name="DuplicateAttempt",
        )
        assert res["ok"] is False
        assert res["code"] == "email_already_registered"
        assert "already exists" in res["message"]

    def test_register_user_weak_password_fails(self):
        """Verify registration with weak password returns error envelope."""
        res = AccountService.register_user(
            email="weak@example.com",
            password="weak",
            display_name="WeakUser",
        )
        assert res["ok"] is False
        assert res["code"] == "password_too_weak"
        assert len(res["errors"]) > 0

    def test_register_user_invalid_display_name_fails(self):
        """Verify display name with invalid characters or length fails."""
        res_short = AccountService.register_user(
            email="short@example.com",
            password="StrongPassword123!",
            display_name="A",
        )
        assert res_short["ok"] is False
        assert res_short["code"] == "invalid_display_name"

        res_invalid_chars = AccountService.register_user(
            email="chars@example.com",
            password="StrongPassword123!",
            display_name="Bad<script>Name",
        )
        assert res_invalid_chars["ok"] is False
        assert res_invalid_chars["code"] == "invalid_display_name"

    def test_verify_email_token_success(self):
        """Verify submitting valid OTP code consumes token and activates user."""
        reg_res = AccountService.register_user(
            email="verify@example.com",
            password="StrongPassword123!",
            display_name="VerifyMe",
        )
        user = reg_res["user"]
        raw_otp = reg_res["raw_otp"]

        verify_res = AccountService.verify_email_token(
            user=user,
            submitted_code=raw_otp,
        )
        assert verify_res["ok"] is True
        assert verify_res["message"] == "Email successfully verified."

        user.refresh_from_db()
        assert user.email_verified is True

        token = EmailVerificationToken.objects.get(id=reg_res["token_id"])
        assert token.is_consumed is True
        assert token.consumed_at is not None

    def test_verify_email_token_already_consumed_fails(self):
        """Verify re-submitting already consumed token fails."""
        reg_res = AccountService.register_user(
            email="reconsume@example.com",
            password="StrongPassword123!",
            display_name="Reconsume",
        )
        user = reg_res["user"]
        raw_otp = reg_res["raw_otp"]

        # First verification succeeds
        AccountService.verify_email_token(user=user, submitted_code=raw_otp)

        # Second verification fails
        second_res = AccountService.verify_email_token(
            user=user, submitted_code=raw_otp
        )
        assert second_res["ok"] is False
        assert second_res["code"] == "no_active_token"

    def test_verify_email_token_wrong_code_fails(self):
        """Verify submitting mismatched OTP code returns token_invalid."""
        reg_res = AccountService.register_user(
            email="wrongcode@example.com",
            password="StrongPassword123!",
            display_name="WrongCode",
        )
        user = reg_res["user"]

        verify_res = AccountService.verify_email_token(
            user=user,
            submitted_code="999999",
        )
        assert verify_res["ok"] is False
        assert verify_res["code"] == "token_invalid"

        user.refresh_from_db()
        assert user.email_verified is False

    def test_verify_email_token_expired_fails(self):
        """Verify submitting expired OTP code returns token_expired."""
        reg_res = AccountService.register_user(
            email="expired@example.com",
            password="StrongPassword123!",
            display_name="ExpiredUser",
        )
        user = reg_res["user"]
        raw_otp = reg_res["raw_otp"]

        # Manually expire token
        token = EmailVerificationToken.objects.get(id=reg_res["token_id"])
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save()

        verify_res = AccountService.verify_email_token(
            user=user,
            submitted_code=raw_otp,
        )
        assert verify_res["ok"] is False
        assert verify_res["code"] == "token_expired"

    def test_resend_verification_token_lifecycle_and_cap(self):
        """Verify up to 3 resends succeed and 4th attempt is blocked."""
        reg_res = AccountService.register_user(
            email="resendcap@example.com",
            password="StrongPassword123!",
            display_name="ResendCap",
        )
        user = reg_res["user"]
        initial_token_id = reg_res["token_id"]

        # Resend 1
        res1 = AccountService.resend_verification_token(user=user)
        assert res1["ok"] is True
        assert res1["attempts_left"] == 2
        # Prior token should now be expired
        prev_token = EmailVerificationToken.objects.get(id=initial_token_id)
        assert prev_token.is_expired is True

        # Resend 2
        res2 = AccountService.resend_verification_token(user=user)
        assert res2["ok"] is True
        assert res2["attempts_left"] == 1

        # Resend 3
        res3 = AccountService.resend_verification_token(user=user)
        assert res3["ok"] is True
        assert res3["attempts_left"] == 0

        # Resend 4 (exceeds cap)
        res4 = AccountService.resend_verification_token(user=user)
        assert res4["ok"] is False
        assert res4["code"] == "resend_limit_exceeded"
        assert res4["attempts_left"] == 0
        assert "Maximum resend attempts reached" in res4["message"]
