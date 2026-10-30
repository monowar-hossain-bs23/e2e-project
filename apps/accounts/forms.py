"""Forms for Basha Pass authentication, onboarding, and password recovery."""

import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.accounts.validators import PasswordComplexityValidator

DISPLAY_NAME_REGEX = re.compile(r"^[A-Za-z0-9 ._\-']+$")


class SignupForm(forms.Form):
    """Visitor registration form."""

    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "you@example.com",
                "autocomplete": "email",
                "required": "required",
            }
        ),
    )
    display_name = forms.CharField(
        label=_("Display name"),
        min_length=2,
        max_length=32,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Monowar",
                "autocomplete": "nickname",
                "required": "required",
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Choose a password",
                "autocomplete": "new-password",
                "required": "required",
                "id": "password-input",
            }
        ),
    )

    def clean_email(self) -> str:
        """Validate and normalize email."""
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email already exists."))
        return email

    def clean_display_name(self) -> str:
        """Validate display name rules."""
        display_name = self.cleaned_data.get("display_name", "").strip()
        if not DISPLAY_NAME_REGEX.match(display_name):
            raise ValidationError(
                _(
                    "Display name may only contain alphanumeric characters, spaces, "
                    "and basic punctuation (. _ - ')."
                )
            )
        return display_name

    def clean_password(self) -> str:
        """Enforce 5-rule password complexity."""
        password = self.cleaned_data.get("password", "")
        validator = PasswordComplexityValidator()
        validator.validate(password)
        return password


class VerifyEmailForm(forms.Form):
    """Email verification 6-digit OTP submission form."""

    code = forms.CharField(
        label=_("Verification code"),
        min_length=6,
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center fs-3 fw-bold letter-spacing-1",
                "placeholder": "123456",
                "inputmode": "numeric",
                "pattern": "[0-9]{6}",
                "autocomplete": "one-time-code",
                "required": "required",
                "id": "otp-input",
            }
        ),
    )

    def clean_code(self) -> str:
        """Validate that OTP consists of 6 numeric digits."""
        code = self.cleaned_data.get("code", "").strip()
        if not code.isdigit() or len(code) != 6:
            raise ValidationError(_("Verification code must be exactly 6 digits."))
        return code


class LoginForm(forms.Form):
    """Tenant and staff login form."""

    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "you@example.com",
                "autocomplete": "email",
                "required": "required",
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Your password",
                "autocomplete": "current-password",
                "required": "required",
            }
        ),
    )


class PasswordResetRequestForm(forms.Form):
    """Password recovery email request form."""

    email = forms.EmailField(
        label=_("Email address"),
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "you@example.com",
                "autocomplete": "email",
                "required": "required",
            }
        ),
    )


class SetNewPasswordForm(forms.Form):
    """Form to establish a new password from reset link."""

    password = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter new password",
                "autocomplete": "new-password",
                "required": "required",
                "id": "new-password",
            }
        ),
    )
    password_confirm = forms.CharField(
        label=_("Confirm new password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Re-enter new password",
                "autocomplete": "new-password",
                "required": "required",
            }
        ),
    )

    def clean(self) -> dict:
        """Verify matching passwords and complexity requirements."""
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password_confirm")

        if p1 and p2 and p1 != p2:
            raise ValidationError(_("The two passwords do not match."))

        if p1:
            PasswordComplexityValidator().validate(p1)

        return cleaned_data
