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
from apps.audit.services.audit_service import AuditService
from apps.listings.validators import validate_phone_number
from apps.passports.validators import validate_budget_range, validate_dhaka_sub_areas

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

    @classmethod
    def update_profile(
        cls,
        *,
        user: User,
        display_name: str,
        phone_number: str | None = None,
    ) -> dict[str, Any]:
        """Validate and update user public handle and primary contact phone."""
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

        cleaned_phone: str | None = None
        if phone_number and str(phone_number).strip():
            try:
                cleaned_phone = validate_phone_number(str(phone_number).strip())
            except ValidationError as exc:
                return {
                    "ok": False,
                    "code": "invalid_phone_number",
                    "message": exc.messages[0]
                    if hasattr(exc, "messages")
                    else str(exc),
                    "errors": ["phone_number"],
                }

        old_phone = user.phone_number
        user.display_name = display_name
        user.phone_number = cleaned_phone

        with transaction.atomic():
            user.save(update_fields=["display_name", "phone_number", "updated_at"])

            # Sync handle to passport if user already has one
            if hasattr(user, "passport"):
                user.passport.display_name = display_name
                user.passport.save(update_fields=["display_name", "updated_at"])

            # Record audit entry if phone number changed
            if old_phone != cleaned_phone:
                AuditService.append(
                    actor_id=user.id,
                    target=user,
                    action="profile_updated",
                    reason_code="phone_number_changed",
                    before_state={"phone_number": old_phone},
                    after_state={"phone_number": cleaned_phone},
                )

        logger.info("User profile updated: user_id=%s", user.id)
        return {"ok": True, "user": user}

    @classmethod
    def update_location_preferences(
        cls,
        *,
        user: User,
        area_preference: list[str],
        budget_min: int,
        budget_max: int,
    ) -> dict[str, Any]:
        """Validate and update tenant search areas and monthly budget limits."""
        if not hasattr(user, "passport") or not hasattr(
            user.passport, "lifestyle_profile"
        ):
            return {
                "ok": False,
                "code": "missing_profile",
                "message": "User does not have an active lifestyle profile.",
                "errors": ["lifestyle_profile"],
            }

        try:
            validate_dhaka_sub_areas(area_preference)
            validate_budget_range(budget_min, budget_max)
        except ValidationError as exc:
            return {
                "ok": False,
                "code": "invalid_parameters",
                "message": exc.messages[0] if hasattr(exc, "messages") else str(exc),
                "errors": [
                    "area_preference" if "area" in str(exc).lower() else "budget"
                ],
            }

        profile = user.passport.lifestyle_profile
        profile.area_preference = area_preference
        profile.budget_min = budget_min
        profile.budget_max = budget_max

        with transaction.atomic():
            profile.full_clean()
            profile.save(
                update_fields=[
                    "area_preference",
                    "budget_min",
                    "budget_max",
                    "updated_at",
                ]
            )

        logger.info(
            "Location preferences updated: user_id=%s, areas=%s",
            user.id,
            area_preference,
        )
        return {"ok": True, "profile": profile}

    @classmethod
    def change_password(
        cls,
        *,
        user: User,
        current_password: str,
        new_password: str,
    ) -> dict[str, Any]:
        """Verify current password, validate complexity, and update password hash."""
        if not user.check_password(current_password):
            return {
                "ok": False,
                "code": "invalid_current_password",
                "message": "Your current password was entered incorrectly.",
                "errors": ["current_password"],
            }

        validator = PasswordComplexityValidator()
        try:
            validator.validate(new_password)
        except ValidationError as exc:
            return {
                "ok": False,
                "code": "password_too_weak",
                "message": "New password does not meet complexity requirements.",
                "errors": list(exc.messages),
            }

        with transaction.atomic():
            user.set_password(new_password)
            user.save(update_fields=["password", "updated_at"])

            AuditService.append(
                actor_id=user.id,
                target=user,
                action="password_changed",
                reason_code="user_credential_rotation",
                before_state=None,
                after_state={},
            )

        logger.info("User password changed successfully: user_id=%s", user.id)
        return {"ok": True, "user": user}
