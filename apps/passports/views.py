"""Views for Tenant Passport creation wizard and status dashboards."""

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.passports.forms import PassportSubmissionForm
from apps.passports.models import LifestyleProfile, Passport
from apps.passports.validators import (
    DHAKA_SUB_AREAS,
    MAX_BUDGET_BDT,
    MIN_BUDGET_BDT,
)
from apps.verification.models import Verification
from apps.verification.services.verification_service import VerificationService


class PassportWizardView(LoginRequiredMixin, View):
    """Multi-step onboarding wizard for creating a Tenant Passport (Story 015)."""

    template_name = "passports/wizard.html"

    def get_user_passport(self, user: Any) -> Passport | None:
        return getattr(user, "passport", None)

    def check_guards(self, request: HttpRequest) -> HttpResponse | None:
        """Enforce verified state, pending reviews, and 24-hour cooldown guards."""
        passport = self.get_user_passport(request.user)
        if not passport:
            return None

        if passport.is_verified:
            messages.info(request, _("Your Tenant Passport is already verified."))
            return redirect("dashboard")

        if passport.status == Passport.Status.PENDING:
            messages.info(
                request,
                _("Your verification application is currently under staff review."),
            )
            return redirect("dashboard")

        cooldown = VerificationService.check_cooldown(passport)
        if cooldown["cooldown_active"]:
            hrs = max(1, cooldown["remaining_seconds"] // 3600)
            messages.warning(
                request,
                _(
                    f"A 24-hour waiting period is in place following a rejected "
                    f"submission. Please wait approximately {hrs} hour(s) before "
                    f"submitting new verification documents."
                ),
            )
            return redirect("dashboard")

        return None

    def get_initial_data(self, passport: Passport | None) -> dict[str, Any]:
        """Pre-populate form with existing draft or previously entered details."""
        if not passport:
            return {}
        initial: dict[str, Any] = {"display_name": passport.display_name}
        profile = getattr(passport, "lifestyle_profile", None)
        if profile:
            initial.update(
                {
                    "gender": profile.gender,
                    "occupation": profile.occupation,
                    "smoking": profile.smoking,
                    "sleep_schedule": profile.sleep_schedule,
                    "area_preference": profile.area_preference or [],
                    "budget_min": profile.budget_min,
                    "budget_max": profile.budget_max,
                }
            )
        return initial

    def get(self, request: HttpRequest) -> HttpResponse:
        guard_response = self.check_guards(request)
        if guard_response:
            return guard_response

        passport = self.get_user_passport(request.user)
        initial = self.get_initial_data(passport)
        form = PassportSubmissionForm(user=request.user, initial=initial)

        context = {
            "form": form,
            "dhaka_sub_areas": DHAKA_SUB_AREAS,
            "min_budget": MIN_BUDGET_BDT,
            "max_budget": MAX_BUDGET_BDT,
        }
        return render(request, self.template_name, context)

    def post(self, request: HttpRequest) -> HttpResponse:
        guard_response = self.check_guards(request)
        if guard_response:
            return guard_response

        form = PassportSubmissionForm(request.POST, request.FILES, user=request.user)
        if not form.is_valid():
            context = {
                "form": form,
                "dhaka_sub_areas": DHAKA_SUB_AREAS,
                "min_budget": MIN_BUDGET_BDT,
                "max_budget": MAX_BUDGET_BDT,
            }
            return render(request, self.template_name, context)

        cleaned = form.cleaned_data

        with transaction.atomic():
            passport, _created_p = Passport.objects.get_or_create(
                user=request.user,
                defaults={"display_name": cleaned["display_name"]},
            )
            if passport.display_name != cleaned["display_name"]:
                passport.display_name = cleaned["display_name"]
                passport.save(update_fields=["display_name", "updated_at"])

            profile, _created_pr = LifestyleProfile.objects.get_or_create(
                passport=passport,
                defaults={
                    "gender": cleaned["gender"],
                    "occupation": cleaned["occupation"],
                    "smoking": cleaned["smoking"],
                    "sleep_schedule": cleaned["sleep_schedule"],
                    "area_preference": cleaned["area_preference"],
                    "budget_min": cleaned["budget_min"],
                    "budget_max": cleaned["budget_max"],
                },
            )
            profile.gender = cleaned["gender"]
            profile.occupation = cleaned["occupation"]
            profile.smoking = cleaned["smoking"]
            profile.sleep_schedule = cleaned["sleep_schedule"]
            profile.area_preference = cleaned["area_preference"]
            profile.budget_min = cleaned["budget_min"]
            profile.budget_max = cleaned["budget_max"]
            profile.save()

        # Submit documents to VerificationService
        res = VerificationService.submit_verification(
            passport=passport,
            actor=request.user,
            nid_front_file=cleaned["nid_front"],
            nid_back_file=cleaned["nid_back"],
            selfie_file=cleaned["selfie"],
        )

        if not res.get("ok"):
            form.add_error(None, res.get("message", _("Submission failed.")))
            context = {
                "form": form,
                "dhaka_sub_areas": DHAKA_SUB_AREAS,
                "min_budget": MIN_BUDGET_BDT,
                "max_budget": MAX_BUDGET_BDT,
            }
            return render(request, self.template_name, context)

        messages.success(
            request,
            _("Your identity verification documents have been submitted for review!"),
        )
        return redirect("dashboard")


class DashboardView(LoginRequiredMixin, View):
    """Dynamic tenant dashboard reflecting passport verification state (Story 016)."""

    template_name = "passports/dashboards/dashboard.html"

    def get_dashboard_context(self, user: Any) -> dict[str, Any]:
        passport = getattr(user, "passport", None)
        if not passport:
            return {
                "passport": None,
                "profile": None,
                "verification": None,
                "state": "unverified",
                "cooldown": None,
            }

        profile = getattr(passport, "lifestyle_profile", None)
        latest_verification = (
            Verification.objects.filter(passport=passport)
            .order_by("-submitted_at")
            .first()
        )

        if passport.is_verified:
            state = "verified"
            cooldown = None
        elif passport.status == Passport.Status.PENDING or (
            latest_verification
            and latest_verification.state
            in (Verification.State.SUBMITTED, Verification.State.REVIEWING)
        ):
            state = "pending"
            cooldown = None
        elif passport.status == Passport.Status.REJECTED or (
            latest_verification
            and latest_verification.state == Verification.State.REJECTED
        ):
            state = "rejected"
            cooldown = VerificationService.check_cooldown(passport)
        else:
            state = "unverified"
            cooldown = None

        return {
            "passport": passport,
            "profile": profile,
            "verification": latest_verification,
            "state": state,
            "cooldown": cooldown,
        }

    def get(self, request: HttpRequest) -> HttpResponse:
        context = self.get_dashboard_context(request.user)
        # Support HTMX partial swapping for dynamic status updates
        if request.headers.get("HX-Request") == "true":
            return render(
                request, "passports/dashboards/_status_container.html", context
            )
        return render(request, self.template_name, context)


class DashboardStatusPartialView(LoginRequiredMixin, View):
    """HTMX endpoint polling verification status transitions without full reload."""

    def get(self, request: HttpRequest) -> HttpResponse:
        view = DashboardView()
        context = view.get_dashboard_context(request.user)
        return render(request, "passports/dashboards/_status_container.html", context)
