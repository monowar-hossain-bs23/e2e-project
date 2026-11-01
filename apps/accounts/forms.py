"""Forms for Basha Pass authentication, onboarding, and password recovery."""

import re

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.accounts.validators import PasswordComplexityValidator
from apps.listings.validators import validate_phone_number
from apps.passports.validators import (
    DHAKA_SUB_AREAS,
    validate_budget_range,
    validate_dhaka_sub_areas,
)

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


class ProfileSettingsForm(forms.Form):
    """Form for editing user public display name and contact phone number."""

    display_name = forms.CharField(
        label=_("Display Name"),
        min_length=2,
        max_length=32,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Tanvir H.",
                "autocomplete": "nickname",
                "required": "required",
            }
        ),
    )
    phone_number = forms.CharField(
        label=_("Contact Phone Number"),
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. 01712345678 or +8801712345678",
                "autocomplete": "tel",
            }
        ),
        help_text=_(
            "Shielded by ConsentService: strictly visible to verified flat "
            "seekers; completely hidden from anonymous visitors."
        ),
    )

    def clean_display_name(self) -> str:
        name = self.cleaned_data.get("display_name", "").strip()
        if not DISPLAY_NAME_REGEX.match(name):
            raise ValidationError(
                _(
                    "Display name may only contain alphanumeric characters, "
                    "spaces, and basic punctuation (. _ - ')."
                )
            )
        return name

    def clean_phone_number(self) -> str | None:
        raw = self.cleaned_data.get("phone_number", "").strip()
        if not raw:
            return None
        return validate_phone_number(raw)


class LocationPreferencesForm(forms.Form):
    """Form for customizing preferred Dhaka sub-areas and monthly rent budget."""

    area_preference = forms.MultipleChoiceField(
        label=_("Preferred Dhaka Sub-Areas"),
        choices=[(area, area) for area in DHAKA_SUB_AREAS],
        widget=forms.CheckboxSelectMultiple,
        required=True,
        error_messages={
            "required": _("Please select at least one preferred Dhaka sub-area.")
        },
    )
    budget_min = forms.IntegerField(
        label=_("Minimum Monthly Budget (BDT)"),
        min_value=500,
        max_value=50000,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. 5000",
                "min": 500,
                "max": 50000,
            }
        ),
    )
    budget_max = forms.IntegerField(
        label=_("Maximum Monthly Budget (BDT)"),
        min_value=500,
        max_value=50000,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. 20000",
                "min": 500,
                "max": 50000,
            }
        ),
    )

    def clean_area_preference(self) -> list[str]:
        areas = self.cleaned_data.get("area_preference") or []
        validate_dhaka_sub_areas(areas)
        return areas

    def clean(self) -> dict:
        cleaned = super().clean()
        b_min = cleaned.get("budget_min")
        b_max = cleaned.get("budget_max")
        if b_min is not None and b_max is not None:
            try:
                validate_budget_range(b_min, b_max)
            except ValidationError as exc:
                self.add_error(
                    "budget_max",
                    exc.message if hasattr(exc, "message") else str(exc),
                )
        return cleaned


class AccountPasswordChangeForm(forms.Form):
    """Form for in-app password rotation with current password verification."""

    current_password = forms.CharField(
        label=_("Current Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your current password",
                "autocomplete": "current-password",
                "required": "required",
            }
        ),
    )
    new_password = forms.CharField(
        label=_("New Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Choose a new strong password",
                "autocomplete": "new-password",
                "required": "required",
                "id": "new-password-input",
            }
        ),
        help_text=_(
            "Min 8 chars with uppercase, lowercase, number, and special symbol."
        ),
    )
    confirm_password = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Re-enter your new password",
                "autocomplete": "new-password",
                "required": "required",
            }
        ),
    )

    def __init__(self, *args, user: User | None = None, **kwargs) -> None:
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self) -> str:
        current = self.cleaned_data.get("current_password", "")
        if self.user and not self.user.check_password(current):
            raise ValidationError(_("Your current password was entered incorrectly."))
        return current

    def clean(self) -> dict:
        cleaned = super().clean()
        p1 = cleaned.get("new_password")
        p2 = cleaned.get("confirm_password")

        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", _("The two new passwords do not match."))

        if p1:
            try:
                PasswordComplexityValidator().validate(p1)
            except ValidationError as exc:
                for msg in exc.messages:
                    self.add_error("new_password", msg)

        return cleaned
