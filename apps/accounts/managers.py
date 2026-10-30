"""Custom user manager for Basha Pass."""

from typing import Any

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Custom manager for the User model with email as the unique identifier."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        display_name: str = "",
        **extra_fields: Any,
    ) -> Any:
        """Create and save a standard user with email, password, and display name."""
        if not email:
            raise ValueError("The Email field must be set.")
        if not display_name:
            raise ValueError("The Display Name field must be set.")

        email = self.normalize_email(email).strip().lower()
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("email_verified", False)

        user = self.model(email=email, display_name=display_name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        display_name: str = "Admin",
        **extra_fields: Any,
    ) -> Any:
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("email_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email, password, display_name=display_name, **extra_fields
        )

    def get_by_natural_key(self, email: str) -> Any:
        """Perform case-insensitive lookup by email."""
        return self.get(email__iexact=email.strip().lower())
