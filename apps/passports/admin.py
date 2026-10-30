"""Django Admin configuration for Passports and Lifestyle Profiles."""

from django.contrib import admin

from apps.passports.models import LifestyleProfile, Passport


class LifestyleProfileInline(admin.StackedInline):
    """Inline view of lifestyle preferences on the Passport admin."""

    model = LifestyleProfile
    can_delete = False
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Passport)
class PassportAdmin(admin.ModelAdmin):
    """Admin configuration for Passport aggregate root."""

    list_display = ("display_name", "user_email", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("display_name", "user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [LifestyleProfileInline]

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
