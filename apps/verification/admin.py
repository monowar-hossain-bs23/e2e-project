"""Django Admin configuration for Verification review queue (FR-7, AD-10, ADR-002)."""

from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.verification.models import Verification
from apps.verification.services.verification_service import VerificationService


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    """Staff FIFO review queue for inspecting identity documents."""

    list_display = (
        "id_short",
        "passport_display_name",
        "state_badge",
        "submitted_at",
        "reviewed_by_staff",
        "reject_reason",
    )
    list_filter = ("state", "reject_reason", "submitted_at")
    search_fields = ("passport__display_name", "passport__user__email")
    ordering = ["submitted_at"]  # Strict FIFO queue per FR-7

    readonly_fields = (
        "id",
        "passport",
        "lifestyle_summary",
        "submitted_at",
        "state",
        "reviewed_by",
        "reviewed_at",
        "last_rejection_at",
        "nid_front_preview",
        "nid_back_preview",
        "selfie_preview",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            _("Applicant & Status"),
            {
                "fields": (
                    "passport",
                    "lifestyle_summary",
                    "state",
                    "submitted_at",
                    "reviewed_by",
                    "reviewed_at",
                    "last_rejection_at",
                )
            },
        ),
        (
            _("Private Document Inspection"),
            {
                "description": _(
                    "Documents stored in media_private/ with zero public access. "
                    "Previews streamed via staff-authenticated endpoint."
                ),
                "fields": (
                    "nid_front_preview",
                    "nid_back_preview",
                    "selfie_preview",
                ),
            },
        ),
        (
            _("Review Decision & Notes"),
            {
                "fields": (
                    "reject_reason",
                    "reviewer_notes",
                )
            },
        ),
    )

    actions = ["approve_submissions", "mark_in_review"]

    def save_model(
        self,
        request,
        obj: Verification,
        form,
        change: bool,
    ) -> None:
        """Enforce AD-10: review transitions must flow through VerificationService."""
        if change and obj.reject_reason and obj.state != Verification.State.REJECTED:
            res = VerificationService.transition(
                verification=obj,
                new_state=Verification.State.REJECTED,
                actor=request.user,
                reason=obj.reject_reason,
                notes=obj.reviewer_notes,
            )
            if not res.get("ok"):
                messages.error(
                    request,
                    f"Failed to reject submission: {res.get('message')}",
                )
            else:
                messages.warning(
                    request,
                    f"Verification for {obj.passport.display_name} rejected "
                    f"({obj.get_reject_reason_display()}). 24h cooldown initiated.",
                )
            return

        super().save_model(request, obj, form, change)

    @admin.display(description="ID")
    def id_short(self, obj: Verification) -> str:
        return str(obj.id)[:8]

    @admin.display(description="Tenant Passport")
    def passport_display_name(self, obj: Verification) -> str:
        return obj.passport.display_name

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
            '<span style="background-color: {0}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-weight: 600; font-size: 11px;">{1}</span>',
            color,
            obj.get_state_display(),
        )

    @admin.display(description="Reviewed By")
    def reviewed_by_staff(self, obj: Verification) -> str:
        return obj.reviewed_by.email if obj.reviewed_by else "-"

    @admin.display(description="Lifestyle Preferences")
    def lifestyle_summary(self, obj: Verification) -> str:
        profile = getattr(obj.passport, "lifestyle_profile", None)
        if not profile:
            return _("No lifestyle profile on record.")

        prefs = profile.area_preference or []
        areas = ", ".join(prefs) if prefs else "None"
        b_min = f"{profile.budget_min:,}"
        b_max = f"{profile.budget_max:,}"
        return format_html(
            "<strong>Gender:</strong> {0}<br>"
            "<strong>Occupation:</strong> {1}<br>"
            "<strong>Smoking:</strong> {2}<br>"
            "<strong>Sleep:</strong> {3}<br>"
            "<strong>Budget:</strong> ৳{4} – ৳{5}<br>"
            "<strong>Areas:</strong> {6}",
            profile.get_gender_display(),
            profile.get_occupation_display(),
            profile.get_smoking_display(),
            profile.get_sleep_schedule_display(),
            b_min,
            b_max,
            areas,
        )

    def _render_doc_preview(self, obj: Verification, doc_type: str) -> str:
        rel_path = getattr(obj, f"{doc_type}_path", None)
        if not rel_path:
            return _("No document uploaded.")

        url = reverse(
            "admin_verification_media",
            kwargs={"verification_id": obj.id, "doc_type": doc_type},
        )
        return format_html(
            '<div style="margin-bottom: 8px;">'
            '<a href="{0}" target="_blank" rel="noopener noreferrer">'
            '<img src="{0}" style="max-height: 220px; max-width: 320px;'
            " border: 1px solid #E2E8F0; border-radius: 6px;"
            ' box-shadow: 0 1px 3px rgba(0,0,0,0.1);" />'
            '</a><br><small style="color: #5A6878;">'
            "Click to view full size in new tab</small></div>",
            url,
        )

    @admin.display(description="NID Front")
    def nid_front_preview(self, obj: Verification) -> str:
        return self._render_doc_preview(obj, "nid_front")

    @admin.display(description="NID Back")
    def nid_back_preview(self, obj: Verification) -> str:
        return self._render_doc_preview(obj, "nid_back")

    @admin.display(description="Selfie Holding NID")
    def selfie_preview(self, obj: Verification) -> str:
        return self._render_doc_preview(obj, "selfie")

    @admin.action(description=_("Approve selected verification submissions"))
    def approve_submissions(self, request, queryset):
        success_count = 0
        for verification in queryset:
            res = VerificationService.transition(
                verification=verification,
                new_state=Verification.State.VERIFIED,
                actor=request.user,
            )
            if res.get("ok"):
                success_count += 1
            else:
                messages.error(
                    request,
                    f"Failed to approve {verification}: {res.get('message')}",
                )

        if success_count > 0:
            messages.success(
                request,
                f"Successfully approved {success_count} verification submission(s).",
            )

    @admin.action(description=_("Mark selected submissions as In Review"))
    def mark_in_review(self, request, queryset):
        for verification in queryset:
            VerificationService.transition(
                verification=verification,
                new_state=Verification.State.REVIEWING,
                actor=request.user,
            )
        messages.info(request, "Selected submissions marked as In Review.")
