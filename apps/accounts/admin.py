"""Admin configuration for Accounts context."""

from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import EmailVerificationToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""

    list_display = (
        "email",
        "display_name",
        "email_verified",
        "is_staff",
        "is_active",
        "created_at",
    )
    list_filter = ("email_verified", "is_staff", "is_active", "created_at")
    search_fields = ("email", "display_name")
    ordering = ("-created_at",)
    readonly_fields = ("id", "date_joined", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        (
            "Profile Info",
            {"fields": ("display_name", "email_verified")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "display_name", "password"),
            },
        ),
    )


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin configuration for viewing verification tokens (audit/debug)."""

    list_display = (
        "user",
        "expires_at",
        "consumed_at",
        "resend_count",
        "created_at",
    )
    list_filter = ("consumed_at", "created_at")
    search_fields = ("user__email", "user__display_name")
    readonly_fields = (
        "id",
        "user",
        "token_hash",
        "created_at",
        "expires_at",
        "consumed_at",
        "resend_count",
    )

    def has_add_permission(self, request: Any) -> bool:
        """Tokens are issued solely via AccountService."""
        return False
