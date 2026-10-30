"""Tests for password complexity validator and helper functions."""

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.validators import PasswordComplexityValidator, check_password_rules


class TestPasswordComplexityValidator:
    """Test suite for 5-rule password complexity enforcement."""

    @pytest.fixture
    def validator(self):
        return PasswordComplexityValidator()

    def test_valid_passwords_pass(self, validator):
        """Verify compliant passwords pass validation."""
        valid_passwords = [
            "BashaPass@2026",
            "Dhaka#1234Sublet",
            "Complex!Pass88",
            "Aa1!aaaa",
        ]
        for pwd in valid_passwords:
            validator.validate(pwd)

    def test_password_less_than_8_chars_fails(self, validator):
        """Verify passwords under 8 characters fail validation."""
        with pytest.raises(ValidationError) as exc:
            validator.validate("Aa1!aaa")
        assert any("at least 8 characters" in msg for msg in exc.value.messages)

    def test_password_missing_uppercase_fails(self, validator):
        """Verify passwords without uppercase letters fail validation."""
        with pytest.raises(ValidationError) as exc:
            validator.validate("lowercase123!")
        assert any("uppercase letter" in msg for msg in exc.value.messages)

    def test_password_missing_lowercase_fails(self, validator):
        """Verify passwords without lowercase letters fail validation."""
        with pytest.raises(ValidationError) as exc:
            validator.validate("UPPERCASE123!")
        assert any("lowercase letter" in msg for msg in exc.value.messages)

    def test_password_missing_digit_fails(self, validator):
        """Verify passwords without digits fail validation."""
        with pytest.raises(ValidationError) as exc:
            validator.validate("NoDigitsHere!")
        assert any("number" in msg for msg in exc.value.messages)

    def test_password_missing_symbol_fails(self, validator):
        """Verify passwords without special characters fail validation."""
        with pytest.raises(ValidationError) as exc:
            validator.validate("NoSymbolsHere123")
        assert any("symbol" in msg for msg in exc.value.messages)

    def test_check_password_rules_helper(self):
        """Verify individual rule breakdown returned by helper."""
        res = check_password_rules("Aa1!")
        assert res["min_length"] is False
        assert res["has_upper"] is True
        assert res["has_lower"] is True
        assert res["has_digit"] is True
        assert res["has_symbol"] is True

        res_valid = check_password_rules("ValidPass@123")
        assert all(res_valid.values())

    def test_validator_help_text(self, validator):
        """Verify human-readable help text."""
        help_text = validator.get_help_text()
        assert "at least 8 characters long" in help_text
        assert "uppercase letter" in help_text
