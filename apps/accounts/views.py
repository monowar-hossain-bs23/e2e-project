"""Views for Basha Pass accounts, authentication, OTP verification, and onboarding."""

import logging
from typing import Any

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
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
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.forms import (
    AccountPasswordChangeForm,
    LocationPreferencesForm,
    LoginForm,
    PasswordResetRequestForm,
    ProfileSettingsForm,
    SetNewPasswordForm,
    SignupForm,
    VerifyEmailForm,
)
from apps.accounts.models import EmailVerificationToken, User
from apps.accounts.services.account_service import AccountService
from apps.passports.validators import DHAKA_SUB_AREAS

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


class AccountSettingsView(LoginRequiredMixin, View):
    """Unified Account Settings hub for profile, location preferences, and security."""

    template_name = "accounts/settings.html"
    login_url = "login"

    def _get_context(
        self,
        request: HttpRequest,
        profile_form: ProfileSettingsForm | None = None,
        location_form: LocationPreferencesForm | None = None,
        password_form: AccountPasswordChangeForm | None = None,
        active_tab: str = "profile",
    ) -> dict[str, Any]:
        user = request.user
        passport = getattr(user, "passport", None)
        profile = getattr(passport, "lifestyle_profile", None) if passport else None

        if profile_form is None:
            profile_form = ProfileSettingsForm(
                initial={
                    "display_name": user.display_name,
                    "phone_number": user.phone_number or "",
                }
            )

        if location_form is None:
            if profile:
                location_form = LocationPreferencesForm(
                    initial={
                        "area_preference": profile.area_preference or [],
                        "budget_min": profile.budget_min,
                        "budget_max": profile.budget_max,
                    }
                )
            else:
                location_form = LocationPreferencesForm(
                    initial={
                        "area_preference": [],
                        "budget_min": 5000,
                        "budget_max": 20000,
                    }
                )

        if password_form is None:
            password_form = AccountPasswordChangeForm(user=user)

        return {
            "user": user,
            "passport": passport,
            "lifestyle_profile": profile,
            "has_profile": profile is not None,
            "profile_form": profile_form,
            "location_form": location_form,
            "password_form": password_form,
            "active_tab": active_tab,
            "dhaka_sub_areas": DHAKA_SUB_AREAS,
        }

    def get(self, request: HttpRequest) -> HttpResponse:
        tab = request.GET.get("tab", "profile")
        if tab not in ("profile", "location", "security"):
            tab = "profile"
        context = self._get_context(request, active_tab=tab)
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest) -> HttpResponse:
        form_action = request.POST.get("form_action", "profile")
        user = request.user

        if form_action == "profile":
            form = ProfileSettingsForm(request.POST)
            if form.is_valid():
                res = AccountService.update_profile(
                    user=user,
                    display_name=form.cleaned_data["display_name"],
                    phone_number=form.cleaned_data["phone_number"],
                )
                if res["ok"]:
                    messages.success(
                        request, _("Your profile details have been updated.")
                    )
                    return redirect(reverse("account_settings") + "?tab=profile")
                form.add_error(None, res["message"])
            context = self._get_context(
                request, profile_form=form, active_tab="profile"
            )
            return render(request, self.template_name, context)

        elif form_action == "location":
            form = LocationPreferencesForm(request.POST)
            if form.is_valid():
                res = AccountService.update_location_preferences(
                    user=user,
                    area_preference=form.cleaned_data["area_preference"],
                    budget_min=form.cleaned_data["budget_min"],
                    budget_max=form.cleaned_data["budget_max"],
                )
                if res["ok"]:
                    messages.success(
                        request,
                        _(
                            "Your preferred living areas and budget have been "
                            "updated! Feed match scores are now refreshed."
                        ),
                    )
                    return redirect(reverse("account_settings") + "?tab=location")
                form.add_error(None, res["message"])
            context = self._get_context(
                request, location_form=form, active_tab="location"
            )
            return render(request, self.template_name, context)

        elif form_action == "password":
            form = AccountPasswordChangeForm(request.POST, user=user)
            if form.is_valid():
                res = AccountService.change_password(
                    user=user,
                    current_password=form.cleaned_data["current_password"],
                    new_password=form.cleaned_data["new_password"],
                )
                if res["ok"]:
                    update_session_auth_hash(request, user)
                    messages.success(
                        request,
                        _("Your password has been changed successfully."),
                    )
                    return redirect(reverse("account_settings") + "?tab=security")
                form.add_error(None, res["message"])
            context = self._get_context(
                request, password_form=form, active_tab="security"
            )
            return render(request, self.template_name, context)

        return redirect("account_settings")
