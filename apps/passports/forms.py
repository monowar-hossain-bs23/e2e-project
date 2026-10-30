"""Forms for Tenant Passport creation, lifestyle preferences, and document uploads."""

from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

from apps.core.mixins import LocaleFormMixin
from apps.passports.models import LifestyleProfile, Passport
from apps.passports.validators import (
    DHAKA_SUB_AREAS,
    MAX_BUDGET_BDT,
    MIN_BUDGET_BDT,
    validate_budget_range,
    validate_dhaka_sub_areas,
    validate_passport_display_name,
)
from apps.verification.services.storage import VerificationStorageService


class PassportSubmissionForm(LocaleFormMixin, forms.Form):
    """Multi-step form capturing passport profile, lifestyle preferences, and files."""

    display_name = forms.CharField(
        label=_("Public Handle / Display Name"),
        min_length=3,
        max_length=32,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("e.g. Tanvir Ahmed"),
                "autocomplete": "nickname",
                "required": "required",
            }
        ),
        help_text=_("Shown on verified listings and roommate search. 3–32 characters."),
    )

    # 6 Lifestyle axes
    gender = forms.ChoiceField(
        label=_("Gender"),
        choices=LifestyleProfile.Gender.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    occupation = forms.ChoiceField(
        label=_("Occupation"),
        choices=LifestyleProfile.Occupation.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    smoking = forms.ChoiceField(
        label=_("Smoking Habit"),
        choices=LifestyleProfile.Smoking.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    sleep_schedule = forms.ChoiceField(
        label=_("Sleep Schedule"),
        choices=LifestyleProfile.SleepSchedule.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    area_preference = forms.MultipleChoiceField(
        label=_("Preferred Dhaka Areas"),
        choices=[(area, area) for area in DHAKA_SUB_AREAS],
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        help_text=_("Select at least one preferred area from the canonical 13."),
    )
    budget_min = forms.IntegerField(
        label=_("Minimum Monthly Budget (BDT)"),
        min_value=MIN_BUDGET_BDT,
        max_value=MAX_BUDGET_BDT,
        initial=5000,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "৳5,000"}
        ),
    )
    budget_max = forms.IntegerField(
        label=_("Maximum Monthly Budget (BDT)"),
        min_value=MIN_BUDGET_BDT,
        max_value=MAX_BUDGET_BDT,
        initial=15000,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": "৳15,000"}
        ),
    )

    # Identity verification documents
    nid_front = forms.FileField(
        label=_("NID Card (Front)"),
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/png,image/webp",
            }
        ),
        help_text=_("Clear photo of NID front. JPG, PNG, or WebP up to 5MB."),
    )
    nid_back = forms.FileField(
        label=_("NID Card (Back)"),
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/png,image/webp",
            }
        ),
        help_text=_("Clear photo of NID back. JPG, PNG, or WebP up to 5MB."),
    )
    selfie = forms.FileField(
        label=_("Selfie Holding NID"),
        required=True,
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/png,image/webp",
            }
        ),
        help_text=_(
            "Clear photo of your face holding your NID card next to your face."
        ),
    )

    def __init__(self, *args: Any, user: Any = None, **kwargs: Any) -> None:
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_display_name(self) -> str:
        name = (self.cleaned_data.get("display_name") or "").strip()
        validate_passport_display_name(name)

        existing = Passport.objects.filter(display_name__iexact=name).first()
        if existing and (not self.user or existing.user_id != self.user.id):
            raise ValidationError(
                _("This public handle is already registered by another tenant.")
            )
        return name

    def _validate_uploaded_document(self, field_name: str) -> UploadedFile:
        file = self.cleaned_data.get(field_name)
        if not file:
            raise ValidationError(_("This document is required."))
        try:
            VerificationStorageService.validate_file(file)
        except ValidationError as exc:
            raise ValidationError(exc.messages) from exc
        return file

    def clean_nid_front(self) -> UploadedFile:
        return self._validate_uploaded_document("nid_front")

    def clean_nid_back(self) -> UploadedFile:
        return self._validate_uploaded_document("nid_back")

    def clean_selfie(self) -> UploadedFile:
        return self._validate_uploaded_document("selfie")

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        b_min = cleaned_data.get("budget_min")
        b_max = cleaned_data.get("budget_max")
        areas = cleaned_data.get("area_preference")

        if b_min is not None and b_max is not None:
            try:
                validate_budget_range(b_min, b_max)
            except ValidationError as exc:
                self.add_error("budget_min", exc.messages)

        if areas is not None:
            try:
                validate_dhaka_sub_areas(areas)
            except ValidationError as exc:
                self.add_error("area_preference", exc.messages)

        return cleaned_data
