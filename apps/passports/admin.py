"""Django Admin configuration for Passports and Lifestyle Profiles."""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.passports.models import LifestyleProfile, Passport
from apps.verification.models import Verification


class LifestyleProfileInline(admin.StackedInline):
    """Inline view of lifestyle preferences on the Passport admin."""

    model = LifestyleProfile
    can_delete = False
    extra = 0
    readonly_fields = ("created_at", "updated_at")


class VerificationInline(admin.TabularInline):
    """Inline view of verification attempts on the Passport admin."""

    model = Verification
    extra = 0
    can_delete = False
    show_change_link = True
    readonly_fields = (
        "state_badge",
        "submitted_at",
        "reject_reason",
        "reviewed_by",
        "review_link",
    )
    fields = (
        "state_badge",
        "submitted_at",
        "reject_reason",
        "reviewed_by",
        "review_link",
    )

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Status")
    def state_badge(self, obj: Verification) -> str:
        colors = {
            Verification.State.SUBMITTED: "#0F6E7A",
            Verification.State.REVIEWING: "#B45309",
            Verification.State.VERIFIED: "#16A34A",
            Verification.State.REJECTED: "#DC2626",
        }
        color = colors.get(obj.state, "#5A6878")
        return format_html(
            '<span style="background-color: {0}; color: white; padding: 2px 7px; '
            'border-radius: 10px; font-weight: 600; font-size: 11px;">{1}</span>',
            color,
            obj.get_state_display(),
        )

    @admin.display(description="Review Queue")
    def review_link(self, obj: Verification) -> str:
        if not obj.pk:
            return "-"
        url = reverse("admin:verification_verification_change", args=[obj.pk])
        return format_html(
            '<a class="button" href="{0}" style="font-size: 11px; padding: 3px 8px;">'
            "Review Submission →</a>",
            url,
        )


@admin.register(Passport)
class PassportAdmin(admin.ModelAdmin):
    """Admin configuration for Passport aggregate root."""

    list_display = ("display_name", "user_email", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("display_name", "user__email")
    readonly_fields = ("id", "status", "created_at", "updated_at")
    inlines = [LifestyleProfileInline, VerificationInline]

    @admin.display(description="User Email")
    def user_email(self, obj: Passport) -> str:
        return obj.user.email


@admin.register(LifestyleProfile)
class LifestyleProfileAdmin(admin.ModelAdmin):
    """Admin configuration for standalone LifestyleProfile queries."""

    list_display = (
        "passport_display_name",
        "gender",
        "occupation",
        "smoking",
        "sleep_schedule",
        "budget_range",
    )
    list_filter = ("gender", "occupation", "smoking", "sleep_schedule")
    search_fields = ("passport__display_name", "passport__user__email")
    readonly_fields = ("id", "created_at", "updated_at")

    @admin.display(description="Passport")
    def passport_display_name(self, obj: LifestyleProfile) -> str:
        return obj.passport.display_name

    @admin.display(description="Budget Range (BDT)")
    def budget_range(self, obj: LifestyleProfile) -> str:
        return f"৳{obj.budget_min:,} – ৳{obj.budget_max:,}"
