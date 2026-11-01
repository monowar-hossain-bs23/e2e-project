"""Tests for AccountService business logic and OTP operations."""

from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import EmailVerificationToken, User
from apps.accounts.services.account_service import AccountService
from apps.audit.models import AuditEntry
from apps.passports.models import LifestyleProfile, Passport


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

    def test_update_profile_success_and_audits_phone_change(self):
        """Updating display name and phone number persists and creates audit record."""
        user = User.objects.create_user(
            email="profile_test@example.com",
            password="Password123!",
            display_name="OriginalName",
            phone_number="+8801700000000",
        )
        passport = Passport.objects.create(
            user=user,
            display_name="OriginalName",
            status=Passport.Status.VERIFIED,
        )

        res = AccountService.update_profile(
            user=user,
            display_name="UpdatedHandle",
            phone_number="+8801811223344",
        )
        assert res["ok"] is True
        user.refresh_from_db()
        assert user.display_name == "UpdatedHandle"
        assert user.phone_number == "+8801811223344"

        # Check passport display name synced
        passport.refresh_from_db()
        assert passport.display_name == "UpdatedHandle"

        # Verify audit entry recorded for phone change
        audit = AuditEntry.objects.filter(
            actor_id=user.id, action="profile_updated"
        ).latest("timestamp")
        assert audit.reason_code == "phone_number_changed"
        assert audit.before_state == {"phone_number": "+8801700000000"}
        assert audit.after_state == {"phone_number": "+8801811223344"}

    def test_update_profile_invalid_display_name_fails(self):
        """Invalid display name returns error envelope."""
        user = User.objects.create_user(
            email="invalid_handle@example.com",
            password="Password123!",
            display_name="ValidHandle",
        )
        res = AccountService.update_profile(
            user=user,
            display_name="x",  # Too short (<2)
        )
        assert res["ok"] is False
        assert res["code"] == "invalid_display_name"
        user.refresh_from_db()
        assert user.display_name == "ValidHandle"

    def test_update_profile_invalid_phone_number_fails(self):
        """Invalid phone number returns error envelope."""
        user = User.objects.create_user(
            email="invalid_phone@example.com",
            password="Password123!",
            display_name="ValidHandle",
        )
        res = AccountService.update_profile(
            user=user,
            display_name="ValidHandle",
            phone_number="not-a-phone",
        )
        assert res["ok"] is False
        assert res["code"] == "invalid_phone_number"

    def test_update_location_preferences_success(self):
        """Updating search areas and budget bounds persists to LifestyleProfile."""
        user = User.objects.create_user(
            email="location_pref@example.com",
            password="Password123!",
            display_name="LocUser",
        )
        passport = Passport.objects.create(
            user=user,
            display_name="LocUser",
            status=Passport.Status.VERIFIED,
        )
        profile = LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.STUDENT,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Mirpur"],
            budget_min=5000,
            budget_max=10000,
        )

        res = AccountService.update_location_preferences(
            user=user,
            area_preference=["Dhanmondi", "Mohammadpur"],
            budget_min=8000,
            budget_max=16000,
        )
        assert res["ok"] is True
        profile.refresh_from_db()
        assert profile.area_preference == ["Dhanmondi", "Mohammadpur"]
        assert profile.budget_min == 8000
        assert profile.budget_max == 16000

    def test_update_location_preferences_invalid_sub_area_fails(self):
        """Non-canonical Dhaka sub-area is rejected."""
        user = User.objects.create_user(
            email="bad_area@example.com",
            password="Password123!",
            display_name="BadArea",
        )
        passport = Passport.objects.create(
            user=user,
            display_name="BadArea",
            status=Passport.Status.VERIFIED,
        )
        LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.STUDENT,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Mirpur"],
            budget_min=5000,
            budget_max=10000,
        )

        res = AccountService.update_location_preferences(
            user=user,
            area_preference=["NonExistentArea"],
            budget_min=5000,
            budget_max=10000,
        )
        assert res["ok"] is False
        assert res["code"] == "invalid_parameters"

    def test_update_location_preferences_inverted_budget_fails(self):
        """Budget min > budget max is rejected."""
        user = User.objects.create_user(
            email="bad_budget@example.com",
            password="Password123!",
            display_name="BadBudget",
        )
        passport = Passport.objects.create(
            user=user,
            display_name="BadBudget",
            status=Passport.Status.VERIFIED,
        )
        LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.STUDENT,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Mirpur"],
            budget_min=5000,
            budget_max=10000,
        )

        res = AccountService.update_location_preferences(
            user=user,
            area_preference=["Mirpur"],
            budget_min=20000,
            budget_max=10000,  # Inverted!
        )
        assert res["ok"] is False
        assert res["code"] == "invalid_parameters"

    def test_change_password_success_and_audits(self):
        """Valid password rotation updates hash and logs audit entry."""
        user = User.objects.create_user(
            email="pwd_change@example.com",
            password="OldPassword123!",
            display_name="PwdUser",
        )

        res = AccountService.change_password(
            user=user,
            current_password="OldPassword123!",
            new_password="NewComplexPassword456@",
        )
        assert res["ok"] is True
        user.refresh_from_db()
        assert user.check_password("NewComplexPassword456@") is True
        assert user.check_password("OldPassword123!") is False

        # Verify audit record created with zero plaintext passwords
        audit = AuditEntry.objects.filter(
            actor_id=user.id, action="password_changed"
        ).latest("timestamp")
        assert audit.reason_code == "user_credential_rotation"
        assert audit.after_state == {}

    def test_change_password_incorrect_current_fails(self):
        """Incorrect current password is rejected."""
        user = User.objects.create_user(
            email="pwd_wrong@example.com",
            password="CorrectPassword123!",
            display_name="WrongPwdUser",
        )

        res = AccountService.change_password(
            user=user,
            current_password="WrongPassword123!",
            new_password="NewComplexPassword456@",
        )
        assert res["ok"] is False
        assert res["code"] == "invalid_current_password"
        user.refresh_from_db()
        assert user.check_password("CorrectPassword123!") is True

    def test_change_password_weak_new_password_fails(self):
        """Weak new password is rejected by complexity rules."""
        user = User.objects.create_user(
            email="pwd_weak@example.com",
            password="CorrectPassword123!",
            display_name="WeakPwdUser",
        )

        res = AccountService.change_password(
            user=user,
            current_password="CorrectPassword123!",
            new_password="simple",  # Weak
        )
        assert res["ok"] is False
        assert res["code"] == "password_too_weak"
        assert len(res["errors"]) > 0
