"""Core form mixins for Basha Pass."""

from typing import Any

from django import forms


class LocaleFormMixin:
    """Mixin setting bilingual/locale attributes on text-bearing form fields (AD-13)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for _, field in getattr(self, "fields", {}).items():
            if isinstance(field.widget, forms.TextInput | forms.Textarea):
                existing_class = field.widget.attrs.get("class", "")
                if "font-bengali-ready" not in existing_class:
                    field.widget.attrs["class"] = (
                        f"{existing_class} font-bengali-ready".strip()
                    )
                field.widget.attrs.setdefault("lang", "auto")
