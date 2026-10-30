"""Views for Basha Pass accounts, authentication, OTP verification, and onboarding."""

import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import (
    url_has_allowed_host_and_scheme,
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.forms import (
    LoginForm,
    PasswordResetRequestForm,
    SetNewPasswordForm,
    SignupForm,
    VerifyEmailForm,
)
from apps.accounts.models import EmailVerificationToken, User
from apps.accounts.services.account_service import AccountService

logger = logging.getLogger(__name__)

SESSION_PENDING_USER_ID = "pending_verification_user_id"
SESSION_PENDING_EMAIL = "pending_verification_email"


def get_pending_user(request: HttpRequest) -> User | None:
    """Retrieve user undergoing email verification from session or request."""
    if request.user.is_authenticated and not request.user.email_verified:
        return request.user

    user_id = request.session.get(SESSION_PENDING_USER_ID)
    if user_id:
        try:
            return User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError):
            return None
    return None


class SignupView(View):
    """Visitor registration view."""

    template_name = "accounts/signup.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("/")
        form = SignupForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("/")

        form = SignupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        display_name = form.cleaned_data["display_name"]

        result = AccountService.register_user(
            email=email,
            password=password,
            display_name=display_name,
        )

        if not result["ok"]:
            form.add_error(None, result["message"])
            return render(request, self.template_name, {"form": form})

        user = result["user"]
        request.session[SESSION_PENDING_USER_ID] = str(user.id)
        request.session[SESSION_PENDING_EMAIL] = user.email

        messages.info(
            request,
            f"We've sent a 6-digit verification code to {user.email}.",
        )
        return redirect("verify_email")


class VerifyEmailView(View):
    """Email OTP verification screen."""

    template_name = "accounts/verify_email.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        user = get_pending_user(request)
        if not user:
            messages.warning(request, "Please sign up or log in first.")
            return redirect("signup")

        if user.email_verified:
            return redirect("welcome")

        form = VerifyEmailForm()
        latest_token = (
            EmailVerificationToken.objects.filter(user=user)
            .order_by("-created_at")
            .first()
        )
        resend_count = latest_token.resend_count if latest_token else 0
        attempts_left = max(0, 3 - resend_count)

        context = {
            "form": form,
            "target_email": user.email,
            "attempts_left": attempts_left,
        }
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest) -> HttpResponse:
        user = get_pending_user(request)
        if not user:
            messages.warning(
                request, "Your verification session expired. Please log in."
            )
            return redirect("login")

        form = VerifyEmailForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form, "target_email": user.email, "attempts_left": 3},
            )

        code = form.cleaned_data["code"]
        result = AccountService.verify_email_token(user=user, submitted_code=code)

        if not result["ok"]:
            form.add_error("code", result["message"])
            latest_token = (
                EmailVerificationToken.objects.filter(user=user)
                .order_by("-created_at")
                .first()
            )
            resend_count = latest_token.resend_count if latest_token else 0
            attempts_left = max(0, 3 - resend_count)

            return render(
                request,
                self.template_name,
                {
                    "form": form,
                    "target_email": user.email,
                    "attempts_left": attempts_left,
                    "error_code": result.get("code"),
                },
            )

        # Authenticate session
        login(
            request,
            user,
            backend="apps.accounts.backends.CaseInsensitiveModelBackend",
        )
        request.session.pop(SESSION_PENDING_USER_ID, None)
        request.session.pop(SESSION_PENDING_EMAIL, None)

        messages.success(request, "Email verified successfully!")
        return redirect("welcome")


class ResendOTPView(View):
    """Endpoint for triggering a new OTP token via HTMX or standard POST."""

    def post(self, request: HttpRequest) -> HttpResponse:
        user = get_pending_user(request)
        if not user:
            if request.headers.get("HX-Request"):
                return HttpResponse(
                    "<div class='alert alert-warning py-2 small'>"
                    "Session expired. Please log in.</div>"
                )
            return redirect("login")

        result = AccountService.resend_verification_token(user=user)

        if request.headers.get("HX-Request"):
            return render(
                request,
                "accounts/partials/resend_status.html",
                {"result": result, "attempts_left": result.get("attempts_left", 0)},
            )

        if result["ok"]:
            left = result["attempts_left"]
            messages.success(
                request,
                f"New verification code sent! ({left} resends remaining)",
            )
        else:
            messages.error(request, result["message"])

        return redirect("verify_email")


class LoginView(View):
    """User login view with 30-day session persistence."""

    template_name = "accounts/login.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("/")
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("/")

        form = LoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        email = form.cleaned_data["email"].strip().lower()
        password = form.cleaned_data["password"]

        user = authenticate(request, email=email, password=password)

        if user is None:
            form.add_error(None, "Invalid email or password.")
            return render(request, self.template_name, {"form": form})

        if not user.email_verified:
            request.session[SESSION_PENDING_USER_ID] = str(user.id)
            request.session[SESSION_PENDING_EMAIL] = user.email
            messages.warning(
                request,
                "Please verify your email address to access your account.",
            )
            return redirect("verify_email")

        login(
            request,
            user,
            backend="apps.accounts.backends.CaseInsensitiveModelBackend",
        )

        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)
        return redirect("dashboard")


class LogoutView(View):
    """Log out the current user session."""

    def post(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect("/")

    def get(self, request: HttpRequest) -> HttpResponse:
        """Allow GET for convenience, redirecting to landing."""
        logout(request)
        return redirect("/")


class WelcomeView(LoginRequiredMixin, TemplateView):
    """Onboarding welcome screen post-verification."""

    template_name = "accounts/welcome.html"


class PasswordResetRequestView(View):
    """Initiate password recovery."""

    template_name = "accounts/password_reset.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        form = PasswordResetRequestForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = PasswordResetRequestForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        email = form.cleaned_data["email"].strip().lower()
        users = User.objects.filter(email__iexact=email, is_active=True)

        for user in users:
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                reverse(
                    "password_reset_confirm",
                    kwargs={"uidb64": uidb64, "token": token},
                )
            )

            subject = "Reset your Basha Pass password"
            message = (
                f"Hello {user.display_name},\n\n"
                f"Click the link below to reset your password:\n{reset_url}\n\n"
                f"If you did not request this, you can ignore this email."
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[user.email],
                fail_silently=True,
            )

        # Always redirect to prevent user enumeration
        return redirect("password_reset_done")


class PasswordResetDoneView(TemplateView):
    """Confirmation message that reset link was sent."""

    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(View):
    """Set new password using reset token."""

    template_name = "accounts/password_reset_confirm.html"

    def _get_user(self, uidb64: str) -> User | None:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return None

    def get(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        user = self._get_user(uidb64)
        validlink = bool(
            user is not None and default_token_generator.check_token(user, token)
        )
        form = SetNewPasswordForm() if validlink else None
        return render(
            request,
            self.template_name,
            {"form": form, "validlink": validlink},
        )

    def post(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        user = self._get_user(uidb64)
        if not user or not default_token_generator.check_token(user, token):
            return render(
                request,
                self.template_name,
                {"form": None, "validlink": False},
            )

        form = SetNewPasswordForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form, "validlink": True},
            )

        new_password = form.cleaned_data["password"]
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        messages.success(request, "Password reset successfully! Please log in.")
        return redirect("password_reset_complete")


class PasswordResetCompleteView(TemplateView):
    """Success confirmation after password reset."""

    template_name = "accounts/password_reset_complete.html"
