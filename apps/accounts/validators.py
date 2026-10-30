"""Password complexity validator adhering to Basha Pass PRD §4.1."""

import re
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

SPECIAL_CHARACTERS = r"""!@#$%^&*(),.?":{}|<>"""


def check_password_rules(password: str) -> dict[str, bool]:
    """Evaluate password against individual complexity rules.

    Returns a dictionary of rule names to boolean pass/fail status.
    """
    return {
        "min_length": len(password) >= 8,
        "has_upper": bool(re.search(r"[A-Z]", password)),
        "has_lower": bool(re.search(r"[a-z]", password)),
        "has_digit": bool(re.search(r"[0-9]", password)),
        "has_symbol": bool(any(c in SPECIAL_CHARACTERS for c in password)),
    }


class PasswordComplexityValidator:
    """Validate that passwords meet the 5 mandatory complexity rules:

    1. At least 8 characters long
    2. At least one uppercase letter
    3. At least one lowercase letter
    4. At least one number
    5. At least one special symbol
    """

    def validate(self, password: str, user: Any = None) -> None:
        """Validate password against the 5 rules, raising ValidationError on failure."""
        rules = check_password_rules(password)
        errors = []

        if not rules["min_length"]:
            errors.append(_("Password must be at least 8 characters long."))
        if not rules["has_upper"]:
            errors.append(
                _("Password must contain at least one uppercase letter (A-Z).")
            )
        if not rules["has_lower"]:
            errors.append(
                _("Password must contain at least one lowercase letter (a-z).")
            )
        if not rules["has_digit"]:
            errors.append(_("Password must contain at least one number (0-9)."))
        if not rules["has_symbol"]:
            errors.append(
                _("Password must contain at least one symbol (e.g. ! @ # $ % ^ & *).")
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self) -> str:
        """Return human-readable instructions for the password rules."""
        return _(
            "Your password must be at least 8 characters long and contain at least one "
            "uppercase letter, one lowercase letter, one number, and one symbol."
        )
