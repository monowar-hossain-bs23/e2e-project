"""Django Admin configuration for Audit entries."""

from django.contrib import admin

from apps.audit.models import AuditEntry


@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    """Read-only admin interface for viewing compliance audit entries."""

    list_display = (
        "timestamp",
        "action",
        "target_type",
        "target_id",
        "actor_id",
        "reason_code",
    )
    list_filter = ("action", "target_type", "timestamp")
    search_fields = ("target_id", "actor_id", "reason_code")
    readonly_fields = (
        "id",
        "actor_id",
        "target_type",
        "target_id",
        "action",
        "before_state",
        "after_state",
        "reason_code",
        "timestamp",
    )

    def has_add_permission(self, request) -> bool:
        """Prevent manual addition via admin."""
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Prevent manual deletion via admin."""
        return False
