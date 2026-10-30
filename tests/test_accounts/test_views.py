"""Integration tests for Accounts views, authentication flow, and OTP onboarding."""

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.accounts.models import EmailVerificationToken, User
from apps.accounts.services.account_service import AccountService
from apps.accounts.views import SESSION_PENDING_EMAIL, SESSION_PENDING_USER_ID


@pytest.mark.django_db
class TestSignupView:
    """Tests for visitor registration."""

    url = reverse("signup")

    def test_signup_get(self, client):
        """GET /accounts/signup/ renders signup form."""
        response = client.get(self.url)
        assert response.status_code == 200
        assert "accounts/signup.html" in [t.name for t in response.templates]
        assert "form" in response.context

    def test_signup_get_authenticated(self, client):
        """Authenticated user accessing signup is redirected to home."""
        user = User.objects.create_user(
            email="auth@example.com",
            password="StrongPassword123!",
            display_name="AuthUser",
        )
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.url == "/"

    def test_signup_post_valid(self, client):
        """POST valid registration creates unverified user and sets pending session."""
        payload = {
            "display_name": "TestTenant",
            "email": "tenant@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }
        response = client.post(self.url, data=payload)
        assert response.status_code == 302
        assert response.url == reverse("verify_email")

        # Verify user created in DB as unverified
        user = User.objects.get(email="tenant@example.com")
        assert user.display_name == "TestTenant"
        assert user.email_verified is False

        # Verify session variables set
        session = client.session
        assert session.get(SESSION_PENDING_USER_ID) == str(user.id)
        assert session.get(SESSION_PENDING_EMAIL) == "tenant@example.com"

        # Verify email dispatched
        assert len(mail.outbox) == 1
        assert "Your Basha Pass Verification Code" in mail.outbox[0].subject

    def test_signup_post_weak_password(self, client):
        """POST with weak password displays complexity validation errors."""
        payload = {
            "display_name": "WeakPasswordUser",
            "email": "weak@example.com",
            "password": "weak",
        }
        response = client.post(self.url, data=payload)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Password must be at least 8 characters long." in content
        assert not User.objects.filter(email="weak@example.com").exists()

    def test_signup_post_duplicate_email(self, client):
        """POST with existing email fails with message."""
        User.objects.create_user(
            email="existing@example.com",
            password="StrongPassword123!",
            display_name="ExistingUser",
        )
        payload = {
            "display_name": "DuplicateUser",
            "email": "existing@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }
        response = client.post(self.url, data=payload)
        assert response.status_code == 200
        assert "already exists" in response.content.decode()


@pytest.mark.django_db
class TestVerifyEmailView:
    """Tests for email OTP verification view."""

    url = reverse("verify_email")

    def test_verify_email_get_no_session(self, client):
        """Accessing verify-email without pending session redirects to signup."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.url == reverse("signup")

    def test_verify_email_get_with_pending_session(self, client):
        """Accessing verify-email with pending session renders form and email."""
        user = User.objects.create_user(
            email="verify_test@example.com",
            password="StrongPassword123!",
            display_name="VerifyTest",
        )
        session = client.session
        session[SESSION_PENDING_USER_ID] = str(user.id)
        session[SESSION_PENDING_EMAIL] = user.email
        session.save()

        response = client.get(self.url)
        assert response.status_code == 200
        assert "accounts/verify_email.html" in [t.name for t in response.templates]
        assert response.context["target_email"] == "verify_test@example.com"
        assert response.context["attempts_left"] == 3

    def test_verify_email_get_already_verified(self, client):
        """Accessing verify-email when user is already verified redirects to welcome."""
        user = User.objects.create_user(
            email="verified@example.com",
            password="StrongPassword123!",
            display_name="VerifiedUser",
            email_verified=True,
        )
        session = client.session
        session[SESSION_PENDING_USER_ID] = str(user.id)
        session.save()

        response = client.get(self.url)
        assert response.status_code == 302
        assert response.url == reverse("welcome")

    def test_verify_email_post_no_session(self, client):
        """POST without pending session redirects to login."""
        response = client.post(self.url, data={"code": "123456"})
        assert response.status_code == 302
        assert response.url == reverse("login")

    def test_verify_email_post_invalid_code(self, client):
        """POST with invalid OTP renders error message."""
        res = AccountService.register_user(
            email="invalid_otp@example.com",
            password="StrongPassword123!",
            display_name="InvalidOTPUser",
        )
        user = res["user"]
        session = client.session
        session[SESSION_PENDING_USER_ID] = str(user.id)
        session.save()

        response = client.post(self.url, data={"code": "000000"})
        assert response.status_code == 200
        assert "Invalid verification code" in response.content.decode()

        user.refresh_from_db()
        assert user.email_verified is False

    def test_verify_email_post_valid_code(self, client):
        """POST with correct OTP verifies user, logs them in, redirects to welcome."""
        res = AccountService.register_user(
            email="valid_otp@example.com",
            password="StrongPassword123!",
            display_name="ValidOTPUser",
        )
        user = res["user"]
        raw_otp = res["raw_otp"]

        session = client.session
        session[SESSION_PENDING_USER_ID] = str(user.id)
        session[SESSION_PENDING_EMAIL] = user.email
        session.save()

        response = client.post(self.url, data={"code": raw_otp})
        assert response.status_code == 302
        assert response.url == reverse("welcome")

        # User is marked verified
        user.refresh_from_db()
        assert user.email_verified is True

        # Session pending keys cleared
        assert SESSION_PENDING_USER_ID not in client.session

        # User is authenticated in session
        assert str(client.session["_auth_user_id"]) == str(user.pk)


@pytest.mark.django_db
class TestResendOTPView:
    """Tests for OTP resend endpoint."""

    url = reverse("resend_otp")

    def test_resend_otp_no_session(self, client):
        """Standard POST without pending session redirects to login."""
        response = client.post(self.url)
        assert response.status_code == 302
        assert response.url == reverse("login")

    def test_resend_otp_htmx_no_session(self, client):
        """HTMX POST without pending session returns warning alert."""
        response = client.post(self.url, HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        assert "Session expired" in response.content.decode()

    def test_resend_otp_standard_post_success(self, client):
        """Standard POST generates new OTP and redirects to verify_email."""
        res = AccountService.register_user(
            email="resend_std@example.com",
            password="StrongPassword123!",
            display_name="ResendStd",
        )
        user = res["user"]
        session = client.session
        session[SESSION_PENDING_USER_ID] = str(user.id)
        session.save()

        # Initial mail count is 1
        assert len(mail.outbox) == 1

        response = client.post(self.url)
        assert response.status_code == 302
        assert response.url == reverse("verify_email")

        # A new email was dispatched
        assert len(mail.outbox) == 2

    def test_resend_otp_htmx_post_success(self, client):
        """HTMX POST returns rendered partial with updated resend count."""
        res = AccountService.register_user(
            email="resend_htmx@example.com",
            password="StrongPassword123!",
            display_name="ResendHtmx",
        )
        user = res["user"]
        session = client.session
        session[SESSION_PENDING_USER_ID] = str(user.id)
        session.save()

        response = client.post(self.url, HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        assert "accounts/partials/resend_status.html" in [
            t.name for t in response.templates
        ]
        assert "Resend code (2 left)" in response.content.decode()

    def test_resend_otp_exceeds_max_resends(self, client):
        """Exceeding 3 resends blocks further attempts."""
        res = AccountService.register_user(
            email="resend_limit@example.com",
            password="StrongPassword123!",
            display_name="ResendLimit",
        )
        user = res["user"]
        session = client.session
        session[SESSION_PENDING_USER_ID] = str(user.id)
        session.save()

        token = EmailVerificationToken.objects.get(id=res["token_id"])
        token.resend_count = 3
        token.save(update_fields=["resend_count"])

        response = client.post(self.url, HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        assert "Resend limit reached" in response.content.decode()


@pytest.mark.django_db
class TestLoginView:
    """Tests for user login view."""

    url = reverse("login")

    def test_login_get(self, client):
        """GET /accounts/login/ renders login form."""
        response = client.get(self.url)
        assert response.status_code == 200
        assert "accounts/login.html" in [t.name for t in response.templates]
        assert "form" in response.context

    def test_login_get_authenticated(self, client):
        """Authenticated user accessing login is redirected to home."""
        user = User.objects.create_user(
            email="login_auth@example.com",
            password="StrongPassword123!",
            display_name="LoginAuth",
            email_verified=True,
        )
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.url == "/"

    def test_login_post_invalid_credentials(self, client):
        """POST with wrong password fails with error message."""
        User.objects.create_user(
            email="user@example.com",
            password="CorrectPassword123!",
            display_name="User",
            email_verified=True,
        )
        payload = {"email": "user@example.com", "password": "WrongPassword!"}
        response = client.post(self.url, data=payload)
        assert response.status_code == 200
        assert "Invalid email or password." in response.content.decode()

    def test_login_post_unverified_user(self, client):
        """POST for unverified user redirects to verify_email with pending session."""
        User.objects.create_user(
            email="unverified_login@example.com",
            password="StrongPassword123!",
            display_name="UnverifiedLogin",
            email_verified=False,
        )
        payload = {
            "email": "unverified_login@example.com",
            "password": "StrongPassword123!",
        }
        response = client.post(self.url, data=payload)
        assert response.status_code == 302
        assert response.url == reverse("verify_email")

        # Session should contain pending user ID
        assert SESSION_PENDING_USER_ID in client.session

    def test_login_post_verified_user_success(self, client):
        """POST for verified user logs in and redirects to dashboard."""
        user = User.objects.create_user(
            email="verified_login@example.com",
            password="StrongPassword123!",
            display_name="VerifiedLogin",
            email_verified=True,
        )
        payload = {
            "email": "VERIFIED_LOGIN@EXAMPLE.COM",
            "password": "StrongPassword123!",
        }
        response = client.post(self.url, data=payload)
        assert response.status_code == 302
        assert response.url == reverse("dashboard")

        # User is authenticated
        assert str(client.session["_auth_user_id"]) == str(user.pk)

    def test_login_post_redirects_to_next(self, client):
        """Login respects valid next query parameter."""
        User.objects.create_user(
            email="next_param@example.com",
            password="StrongPassword123!",
            display_name="NextParam",
            email_verified=True,
        )
        payload = {
            "email": "next_param@example.com",
            "password": "StrongPassword123!",
        }
        response = client.post(f"{self.url}?next=/accounts/welcome/", data=payload)
        assert response.status_code == 302
        assert response.url == "/accounts/welcome/"

    def test_login_post_ignores_malicious_next(self, client):
        """Login rejects off-site next redirect target."""
        User.objects.create_user(
            email="safe_redirect@example.com",
            password="StrongPassword123!",
            display_name="SafeRedirect",
            email_verified=True,
        )
        payload = {
            "email": "safe_redirect@example.com",
            "password": "StrongPassword123!",
        }
        response = client.post(
            f"{self.url}?next=https://malicious-site.example.com", data=payload
        )
        assert response.status_code == 302
        assert response.url == reverse("dashboard")


@pytest.mark.django_db
class TestLogoutView:
    """Tests for user logout view."""

    url = reverse("logout")

    def test_logout_post(self, client):
        """POST /accounts/logout/ logs out user and redirects to home."""
        user = User.objects.create_user(
            email="logout_user@example.com",
            password="StrongPassword123!",
            display_name="LogoutUser",
            email_verified=True,
        )
        client.force_login(user)
        assert "_auth_user_id" in client.session

        response = client.post(self.url)
        assert response.status_code == 302
        assert response.url == "/"
        assert "_auth_user_id" not in client.session

    def test_logout_get(self, client):
        """GET /accounts/logout/ also logs out user and redirects to home."""
        user = User.objects.create_user(
            email="logout_get@example.com",
            password="StrongPassword123!",
            display_name="LogoutGet",
            email_verified=True,
        )
        client.force_login(user)

        response = client.get(self.url)
        assert response.status_code == 302
        assert response.url == "/"
        assert "_auth_user_id" not in client.session


@pytest.mark.django_db
class TestWelcomeView:
    """Tests for post-verification onboarding welcome screen."""

    url = reverse("welcome")

    def test_welcome_unauthenticated(self, client):
        """Unauthenticated visitor is redirected to login."""
        response = client.get(self.url)
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={self.url}"

    def test_welcome_authenticated(self, client):
        """Authenticated user receives 200 on welcome view."""
        user = User.objects.create_user(
            email="welcome_user@example.com",
            password="StrongPassword123!",
            display_name="WelcomeUser",
            email_verified=True,
        )
        client.force_login(user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "accounts/welcome.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestPasswordResetViews:
    """Tests for password recovery views."""

    def test_password_reset_request_get(self, client):
        """GET /accounts/password-reset/ renders request form."""
        response = client.get(reverse("password_reset"))
        assert response.status_code == 200
        assert "accounts/password_reset.html" in [t.name for t in response.templates]

    def test_password_reset_request_post_existing_user(self, client):
        """POST with registered email dispatches reset email and redirects to done."""
        user = User.objects.create_user(
            email="reset_target@example.com",
            password="StrongPassword123!",
            display_name="ResetTarget",
        )
        response = client.post(
            reverse("password_reset"),
            data={"email": "RESET_TARGET@example.com"},
        )
        assert response.status_code == 302
        assert response.url == reverse("password_reset_done")

        # Check mail was sent
        assert len(mail.outbox) == 1
        assert "Reset your Basha Pass password" in mail.outbox[0].subject
        assert user.email in mail.outbox[0].to

    def test_password_reset_request_post_nonexistent_email(self, client):
        """POST with unknown email redirects to done without sending email."""
        response = client.post(
            reverse("password_reset"),
            data={"email": "nobody@example.com"},
        )
        assert response.status_code == 302
        assert response.url == reverse("password_reset_done")
        assert len(mail.outbox) == 0

    def test_password_reset_confirm_get_valid_token(self, client):
        """GET confirm with valid uidb64 and token renders password reset form."""
        user = User.objects.create_user(
            email="confirm_user@example.com",
            password="StrongPassword123!",
            display_name="ConfirmUser",
        )
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": token},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["validlink"] is True
        assert "form" in response.context

    def test_password_reset_confirm_get_invalid_token(self, client):
        """GET confirm with invalid token displays invalid link notice."""
        user = User.objects.create_user(
            email="invalid_token@example.com",
            password="StrongPassword123!",
            display_name="InvalidTokenUser",
        )
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": "invalid-token-123"},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["validlink"] is False

    def test_password_reset_confirm_post_success(self, client):
        """POST confirm updates password and redirects to complete."""
        user = User.objects.create_user(
            email="reset_success@example.com",
            password="OldPassword123!",
            display_name="ResetSuccess",
        )
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": uidb64, "token": token},
        )
        payload = {
            "password": "NewStrongPassword456!",
            "password_confirm": "NewStrongPassword456!",
        }
        response = client.post(url, data=payload)
        assert response.status_code == 302
        assert response.url == reverse("password_reset_complete")

        # Verify new password works
        user.refresh_from_db()
        assert user.check_password("NewStrongPassword456!")
