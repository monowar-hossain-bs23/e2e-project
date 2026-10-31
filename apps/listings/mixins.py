"""Authorization mixins for listing authoring and management (Story 020)."""

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from apps.passports.models import Passport


class VerifiedTenantRequiredMixin(LoginRequiredMixin):
    """Guard mixin ensuring only verified tenants access listing authoring views.

    Unverified, pending, or rejected users are gracefully redirected with
    instructional messages rather than encountering raw authorization failures.
    """

    unverified_redirect_url = reverse_lazy("passport_create")
    review_redirect_url = reverse_lazy("dashboard")

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        try:
            passport = getattr(request.user, "passport", None)
        except ObjectDoesNotExist:
            passport = None

        if passport is None or passport.status == Passport.Status.UNVERIFIED:
            messages.warning(
                request,
                _(
                    "Please complete your Tenant Passport verification "
                    "before posting a listing."
                ),
            )
            return redirect(self.unverified_redirect_url)

        if passport.status == Passport.Status.PENDING:
            messages.info(
                request,
                _(
                    "Your Tenant Passport is currently under review. "
                    "You can create listings as soon as verification is approved."
                ),
            )
            return redirect(self.review_redirect_url)

        if passport.status == Passport.Status.REJECTED:
            messages.warning(
                request,
                _(
                    "Your Tenant Passport verification was not approved. "
                    "Please check your dashboard to review the waiting period."
                ),
            )
            return redirect(self.review_redirect_url)

        if passport.status != Passport.Status.VERIFIED:
            messages.warning(
                request,
                _(
                    "A verified Tenant Passport is required to create "
                    "or manage listings."
                ),
            )
            return redirect(self.review_redirect_url)

        return super().dispatch(request, *args, **kwargs)
