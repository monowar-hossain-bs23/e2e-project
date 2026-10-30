"""Authentication backend supporting case-insensitive email lookup."""

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.http import HttpRequest


class CaseInsensitiveModelBackend(ModelBackend):
    """Authenticates users using email case-insensitively."""

    def authenticate(
        self,
        request: HttpRequest | None = None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Authenticate user by email (case-insensitive) and password."""
        user_model = get_user_model()
        email = kwargs.get("email") or username

        if not email or not password:
            return None

        email = email.strip().lower()
        try:
            user = user_model.objects.get(email__iexact=email)
        except user_model.DoesNotExist:
            # Run password hasher to mitigate timing attacks against non-existent users
            user_model().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
