"""Forms for accommodation listing authoring and management (Story 021, 023)."""

from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.listings.constants import (
    MAX_BODY_LENGTH,
    MAX_LISTING_PHOTOS,
    MAX_RENT_BDT,
    MIN_LISTING_PHOTOS,
    MIN_RENT_BDT,
    PreferredOccupation,
)
from apps.listings.models import Listing
from apps.listings.services.storage import ListingPhotoStorageService
from apps.listings.validators import (
    validate_kind_and_rent_unit,
    validate_phone_number,
)
from apps.passports.validators import DHAKA_SUB_AREAS


class MultipleFileInput(forms.FileInput):
    """HTML file input supporting multiple file selection."""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """FileField supporting multiple uploaded files (Django documentation pattern)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data: Any, initial: Any = None) -> Any:
        single_file_clean = super().clean
        if isinstance(data, list | tuple):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)] if data else []
        return result


class ListingCreationForm(forms.ModelForm):
    """Multi-section creation form for new accommodation listings."""

    area = forms.ChoiceField(
        choices=[(area, area) for area in DHAKA_SUB_AREAS],
        widget=forms.RadioSelect,
        required=True,
        error_messages={"required": _("Please select a Dhaka sub-area.")},
    )
    pref_occupation = forms.MultipleChoiceField(
        choices=PreferredOccupation.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    photos = MultipleFileField(
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "accept": "image/jpeg,image/png,image/webp",
                "class": "d-none",
                "id": "listing-photo-input",
            }
        ),
        required=False,
        help_text=_(
            f"Upload between {MIN_LISTING_PHOTOS} and {MAX_LISTING_PHOTOS} photos. "
            "Landscape (4:3 or 16:9) recommended."
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
                "required": "required",
            }
        ),
        help_text=_(
            "Shielded by ConsentService: only verified flat seekers can view "
            "this phone number. Anonymous visitors cannot see it."
        ),
    )

    class Meta:
        model = Listing
        fields = [
            "kind",
            "area",
            "rent_bdt",
            "rent_unit",
            "body",
            "pref_gender",
            "pref_smoking",
            "pref_sleep",
        ]
        widgets = {
            "kind": forms.Select(attrs={"class": "form-select"}),
            "rent_bdt": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 12000",
                    "min": MIN_RENT_BDT,
                    "max": MAX_RENT_BDT,
                }
            ),
            "rent_unit": forms.Select(attrs={"class": "form-select"}),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "maxlength": MAX_BODY_LENGTH,
                    "placeholder": (
                        "Describe the room, house amenities, bills, "
                        "and expectations for flatmates..."
                    ),
                }
            ),
            "pref_gender": forms.Select(attrs={"class": "form-select"}),
            "pref_smoking": forms.Select(attrs={"class": "form-select"}),
            "pref_sleep": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args: Any, user: Any = None, **kwargs: Any) -> None:
        self.user = user
        super().__init__(*args, **kwargs)
        if self.user and getattr(self.user, "phone_number", None):
            self.fields["phone_number"].initial = self.user.phone_number

    def clean_phone_number(self) -> str:
        """Validate phone format and fallback to user's saved phone if blank."""
        raw = self.cleaned_data.get("phone_number", "").strip()
        if not raw and self.user and getattr(self.user, "phone_number", None):
            raw = self.user.phone_number
        return validate_phone_number(raw)

    def clean_photos(self) -> list[Any]:
        """Validate photo batch count and byte integrity."""
        files = self.cleaned_data.get("photos") or self.files.getlist("photos")
        if not files:
            raise ValidationError(_("At least 1 accommodation photo is required."))

        if len(files) > MAX_LISTING_PHOTOS:
            raise ValidationError(
                _(
                    f"You can upload a maximum of {MAX_LISTING_PHOTOS} photos "
                    f"(uploaded {len(files)})."
                )
            )

        for photo in files:
            ListingPhotoStorageService.validate_photo_file(photo)

        return files

    def clean(self) -> dict[str, Any]:
        """Validate cross-field kind and rent-unit consistency."""
        cleaned_data = super().clean()
        kind = cleaned_data.get("kind")
        rent_unit = cleaned_data.get("rent_unit")

        if kind and rent_unit:
            try:
                validate_kind_and_rent_unit(kind, rent_unit)
            except ValidationError as err:
                self.add_error("rent_unit", err.message)

        return cleaned_data


class ListingEditForm(forms.ModelForm):
    """Form for modifying mutable listing terms with locked-field safety."""

    pref_occupation = forms.MultipleChoiceField(
        choices=PreferredOccupation.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    new_photos = MultipleFileField(
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "accept": "image/jpeg,image/png,image/webp",
                "class": "d-none",
                "id": "listing-photo-input",
            }
        ),
        required=False,
        help_text=_(f"Add additional photos (up to {MAX_LISTING_PHOTOS} total)."),
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
                "required": "required",
            }
        ),
        help_text=_(
            "Shielded by ConsentService: only verified flat seekers can view "
            "this phone number. Anonymous visitors cannot see it."
        ),
    )

    class Meta:
        model = Listing
        fields = [
            "rent_bdt",
            "rent_unit",
            "body",
            "pref_gender",
            "pref_smoking",
            "pref_sleep",
        ]
        widgets = {
            "rent_bdt": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 12000",
                    "min": MIN_RENT_BDT,
                    "max": MAX_RENT_BDT,
                }
            ),
            "rent_unit": forms.Select(attrs={"class": "form-select"}),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "maxlength": MAX_BODY_LENGTH,
                    "placeholder": (
                        "Describe the room, house amenities, bills, "
                        "and expectations for flatmates..."
                    ),
                }
            ),
            "pref_gender": forms.Select(attrs={"class": "form-select"}),
            "pref_smoking": forms.Select(attrs={"class": "form-select"}),
            "pref_sleep": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.pref_occupation:
                self.fields["pref_occupation"].initial = self.instance.pref_occupation
            author_user = getattr(getattr(self.instance, "author", None), "user", None)
            if author_user and getattr(author_user, "phone_number", None):
                self.fields["phone_number"].initial = author_user.phone_number

    def clean_phone_number(self) -> str:
        """Validate phone format and fallback to author's saved phone if blank."""
        raw = self.cleaned_data.get("phone_number", "").strip()
        if not raw and self.instance and self.instance.pk:
            author_user = getattr(getattr(self.instance, "author", None), "user", None)
            if author_user and getattr(author_user, "phone_number", None):
                raw = author_user.phone_number
        return validate_phone_number(raw)

    def clean_new_photos(self) -> list[Any]:
        """Validate newly added photos against maximum limit and magic bytes."""
        files = self.cleaned_data.get("new_photos") or self.files.getlist("new_photos")
        if not files:
            return []

        existing_count = self.instance.photos.count() if self.instance.pk else 0
        total_count = existing_count + len(files)
        if total_count > MAX_LISTING_PHOTOS:
            raise ValidationError(
                _(
                    f"Adding {len(files)} photo(s) would exceed the maximum limit of "
                    f"{MAX_LISTING_PHOTOS} photos ({existing_count} existing)."
                )
            )

        for photo in files:
            ListingPhotoStorageService.validate_photo_file(photo)

        return files

    def clean(self) -> dict[str, Any]:
        """Validate rent unit against immutable instance kind."""
        cleaned_data = super().clean()
        rent_unit = cleaned_data.get("rent_unit")

        if rent_unit and self.instance and self.instance.kind:
            try:
                validate_kind_and_rent_unit(self.instance.kind, rent_unit)
            except ValidationError as err:
                self.add_error("rent_unit", err.message)

        return cleaned_data
