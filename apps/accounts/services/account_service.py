"""AccountService managing user registration, OTP tokens, and email verification."""

import hashlib
import logging
import re
import secrets
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import EmailVerificationToken, User
from apps.accounts.validators import PasswordComplexityValidator

logger = logging.getLogger(__name__)

DISPLAY_NAME_REGEX = re.compile(r"^[A-Za-z0-9 ._\-']+$")
TOKEN_LIFETIME = timedelta(minutes=5)
MAX_RESEND_COUNT = 3


def generate_otp_code() -> str:
    """Generate a cryptographically random 6-digit numeric OTP string."""
    return f"{secrets.randbelow(900000) + 100000:06d}"


def hash_otp_code(raw_otp: str) -> str:
    """Compute the SHA-256 hex digest of a raw OTP string."""
    return hashlib.sha256(raw_otp.encode("utf-8")).hexdigest()


class AccountService:
    """Service layer managing identity lifecycle and verification."""

    @staticmethod
    def register_user(
        *,
        email: str,
        password: str,
        display_name: str,
    ) -> dict[str, Any]:
        """Register a new unverified user and issue their verification token.

        Returns a result envelope dict:
            {'ok': True, 'user': User, 'raw_otp': str, 'token_id': UUID}
            or
            {'ok': False, 'code': str, 'message': str, 'errors': list}
        """
        normalized_email = email.strip().lower()

        # Check existing user
        if User.objects.filter(email__iexact=normalized_email).exists():
            return {
                "ok": False,
                "code": "email_already_registered",
                "message": "An account with this email already exists.",
                "errors": ["email"],
            }

        # Validate display name
        display_name = display_name.strip()
        if (
            len(display_name) < 2
            or len(display_name) > 32
            or not DISPLAY_NAME_REGEX.match(display_name)
        ):
            return {
                "ok": False,
                "code": "invalid_display_name",
                "message": (
                    "Display name must be between 2 and 32 characters and contain only "
                    "alphanumeric characters, spaces, and basic punctuation (. _ - ')."
                ),
                "errors": ["display_name"],
            }

        # Validate password complexity
        validator = PasswordComplexityValidator()
        try:
            validator.validate(password)
        except ValidationError as e:
            return {
                "ok": False,
                "code": "password_too_weak",
                "message": "Password does not meet the complexity requirements.",
                "errors": list(e.messages),
            }

        # Create user and issue initial OTP atomically
        with transaction.atomic():
            user = User.objects.create_user(
                email=normalized_email,
                password=password,
                display_name=display_name,
            )
            raw_otp, token = AccountService.issue_verification_token(
                user=user,
                resend_count=0,
            )

        logger.info(
            "User registered successfully: user_id=%s, email=%s",
            user.id,
            user.email,
        )
        return {
            "ok": True,
            "user": user,
            "raw_otp": raw_otp,
            "token_id": token.id,
        }

    @staticmethod
    def issue_verification_token(
        *,
        user: User,
        resend_count: int = 0,
    ) -> tuple[str, EmailVerificationToken]:
        """Invalidate unconsumed tokens, generate fresh OTP, and dispatch email."""
        now = timezone.now()

        # Invalidate any existing unconsumed tokens
        EmailVerificationToken.objects.filter(
            user=user,
            consumed_at__isnull=True,
            expires_at__gt=now,
        ).update(expires_at=now)

        raw_otp = generate_otp_code()
        token_hash = hash_otp_code(raw_otp)

        token = EmailVerificationToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=now + TOKEN_LIFETIME,
            resend_count=resend_count,
        )

        AccountService._send_verification_email(user=user, raw_otp=raw_otp)
        return raw_otp, token

    @staticmethod
    def verify_email_token(
        *,
        user: User,
        submitted_code: str,
    ) -> dict[str, Any]:
        """Validate submitted 6-digit OTP code against latest active token."""
        code = submitted_code.strip()
        now = timezone.now()

        # Retrieve latest unconsumed token
        token = (
            EmailVerificationToken.objects.filter(
                user=user,
                consumed_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )

        if not token:
            return {
                "ok": False,
                "code": "no_active_token",
                "message": (
                    "No active verification token found. Please request a new code."
                ),
            }

        if now >= token.expires_at:
            return {
                "ok": False,
                "code": "token_expired",
                "message": "Verification code has expired. Please request a new code.",
            }

        submitted_hash = hash_otp_code(code)
        if not secrets.compare_digest(token.token_hash, submitted_hash):
            return {
                "ok": False,
                "code": "token_invalid",
                "message": "Invalid verification code. Please check and try again.",
            }

        # Mark token consumed and user email verified
        with transaction.atomic():
            token.consumed_at = now
            token.save(update_fields=["consumed_at"])

            user.email_verified = True
            user.save(update_fields=["email_verified", "updated_at"])

        logger.info(
            "User email verified: user_id=%s, email=%s",
            user.id,
            user.email,
        )
        return {
            "ok": True,
            "user": user,
            "message": "Email successfully verified.",
        }

    @staticmethod
    def resend_verification_token(
        *,
        user: User,
    ) -> dict[str, Any]:
        """Issue a new verification code if under the maximum resend limit."""
        latest_token = (
            EmailVerificationToken.objects.filter(user=user)
            .order_by("-created_at")
            .first()
        )
        current_resend_count = latest_token.resend_count if latest_token else 0

        if current_resend_count >= MAX_RESEND_COUNT:
            logger.warning(
                "Resend limit exceeded for user_id=%s, count=%d",
                user.id,
                current_resend_count,
            )
            return {
                "ok": False,
                "code": "resend_limit_exceeded",
                "message": "Maximum resend attempts reached. Please restart signup.",
                "attempts_left": 0,
            }

        new_resend_count = current_resend_count + 1
        raw_otp, new_token = AccountService.issue_verification_token(
            user=user,
            resend_count=new_resend_count,
        )

        attempts_left = MAX_RESEND_COUNT - new_resend_count
        logger.info(
            "OTP resent: user_id=%s, count=%d, left=%d",
            user.id,
            new_resend_count,
            attempts_left,
        )
        return {
            "ok": True,
            "attempts_left": attempts_left,
            "raw_otp": raw_otp,
            "token_id": new_token.id,
        }

    @staticmethod
    def _send_verification_email(*, user: User, raw_otp: str) -> None:
        """Render and dispatch transactional email with verification code."""
        context = {
            "user": user,
            "raw_otp": raw_otp,
        }
        subject = "Your Basha Pass Verification Code"
        text_content = render_to_string("accounts/email/verify_email.txt", context)
        html_content = render_to_string("accounts/email/verify_email.html", context)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@bashapass.com")

        send_mail(
            subject=subject,
            message=text_content,
            html_message=html_content,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=False,
        )
