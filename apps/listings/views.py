"""Views for accommodation listing authoring and management (Story 020–023)."""

from typing import Any

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView, UpdateView, View

from apps.listings.constants import MAX_ACTIVE_LISTINGS_PER_USER
from apps.listings.forms import ListingCreationForm, ListingEditForm
from apps.listings.mixins import VerifiedTenantRequiredMixin
from apps.listings.models import Listing
from apps.listings.services.listing_service import ListingService


class ListingCreateView(VerifiedTenantRequiredMixin, FormView):
    """View allowing verified tenants to post a new room or seat listing."""

    template_name = "listings/create.html"
    form_class = ListingCreationForm
    success_url = reverse_lazy("listing_mine")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        passport = self.request.user.passport
        active_count = Listing.objects.filter(
            author=passport,
            archived_at__isnull=True,
            withdrawn_at__isnull=True,
        ).count()

        context["active_count"] = active_count
        context["max_active"] = MAX_ACTIVE_LISTINGS_PER_USER
        context["cap_reached"] = active_count >= MAX_ACTIVE_LISTINGS_PER_USER
        context["remaining_active"] = max(
            0, MAX_ACTIVE_LISTINGS_PER_USER - active_count
        )
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        passport = request.user.passport
        active_count = Listing.objects.filter(
            author=passport,
            archived_at__isnull=True,
            withdrawn_at__isnull=True,
        ).count()

        if active_count >= MAX_ACTIVE_LISTINGS_PER_USER:
            messages.error(
                request,
                _(
                    "You have reached the maximum cap of 3 active listings. "
                    "Please withdraw an existing listing before creating a new one."
                ),
            )
            return redirect(self.success_url)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form: ListingCreationForm) -> HttpResponse:
        passport = self.request.user.passport
        photos = form.cleaned_data.get("photos") or []

        res = ListingService.create(
            author=passport,
            kind=form.cleaned_data["kind"],
            rent_bdt=form.cleaned_data["rent_bdt"],
            rent_unit=form.cleaned_data["rent_unit"],
            area=form.cleaned_data["area"],
            body=form.cleaned_data.get("body"),
            pref_gender=form.cleaned_data.get("pref_gender"),
            pref_smoking=form.cleaned_data.get("pref_smoking"),
            pref_sleep=form.cleaned_data.get("pref_sleep"),
            pref_occupation=form.cleaned_data.get("pref_occupation") or [],
            photo_files=photos,
        )

        if not res.get("ok"):
            messages.error(
                self.request,
                res.get("message", _("Failed to create listing.")),
            )
            return self.form_invalid(form)

        messages.success(
            self.request,
            _("Your accommodation listing has been posted successfully!"),
        )
        return redirect(self.get_success_url())


class ListerDashboardView(VerifiedTenantRequiredMixin, TemplateView):
    """Lister dashboard ("Your Listings") displaying authored accommodation posts."""

    template_name = "listings/mine.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        passport = self.request.user.passport

        all_listings = (
            Listing.objects.filter(author=passport)
            .prefetch_related("photos")
            .order_by("-created_at")
        )

        active_listings = [item for item in all_listings if item.is_active]
        inactive_listings = [item for item in all_listings if not item.is_active]

        tab = self.request.GET.get("tab", "active")
        if tab not in ("active", "inactive"):
            tab = "active"

        displayed_listings = active_listings if tab == "active" else inactive_listings

        active_count = len(active_listings)
        context["listings"] = displayed_listings
        context["active_listings"] = active_listings
        context["inactive_listings"] = inactive_listings
        context["active_count"] = active_count
        context["inactive_count"] = len(inactive_listings)
        context["total_count"] = len(all_listings)
        context["current_tab"] = tab
        context["max_active"] = MAX_ACTIVE_LISTINGS_PER_USER
        context["cap_reached"] = active_count >= MAX_ACTIVE_LISTINGS_PER_USER
        context["remaining_active"] = max(
            0, MAX_ACTIVE_LISTINGS_PER_USER - active_count
        )
        return context


class ListingEditView(VerifiedTenantRequiredMixin, UpdateView):
    """View allowing authors to edit mutable listing terms with locked-field guards."""

    template_name = "listings/edit.html"
    form_class = ListingEditForm
    model = Listing
    pk_url_kwarg = "pk"
    success_url = reverse_lazy("listing_mine")

    def get_object(self, queryset: Any = None) -> Listing:
        listing = super().get_object(queryset)
        if listing.author != self.request.user.passport:
            raise PermissionDenied(
                _("You do not have permission to edit this listing.")
            )
        return listing

    def form_valid(self, form: ListingEditForm) -> HttpResponse:
        listing = self.object
        new_photos = form.cleaned_data.get("new_photos") or []

        delete_photo_ids = self.request.POST.getlist("delete_photos")

        fields = {
            "rent_bdt": form.cleaned_data["rent_bdt"],
            "rent_unit": form.cleaned_data["rent_unit"],
            "body": form.cleaned_data.get("body"),
            "pref_gender": form.cleaned_data.get("pref_gender"),
            "pref_smoking": form.cleaned_data.get("pref_smoking"),
            "pref_sleep": form.cleaned_data.get("pref_sleep"),
            "pref_occupation": form.cleaned_data.get("pref_occupation") or [],
        }

        res = ListingService.edit(
            listing=listing,
            actor=self.request.user,
            fields=fields,
            new_photo_files=new_photos or None,
            delete_photo_ids=delete_photo_ids or None,
        )

        if not res.get("ok"):
            messages.error(
                self.request,
                res.get("message", _("Failed to update listing.")),
            )
            return self.form_invalid(form)

        messages.success(
            self.request,
            _("Your listing terms and details have been updated successfully."),
        )
        return redirect(self.get_success_url())


class ListingWithdrawView(VerifiedTenantRequiredMixin, View):
    """Action endpoint to manually withdraw an active listing."""

    def post(self, request: HttpRequest, pk: Any) -> HttpResponse:
        listing = get_object_or_404(Listing, pk=pk)

        if listing.author != request.user.passport:
            raise PermissionDenied(
                _("You do not have permission to withdraw this listing.")
            )

        res = ListingService.withdraw(listing=listing, actor=request.user)
        if not res.get("ok"):
            messages.error(
                request,
                res.get("message", _("Failed to withdraw listing.")),
            )
        else:
            messages.success(
                request,
                _("Your listing has been withdrawn and is no longer public."),
            )

        return redirect("listing_mine")

    def get(self, request: HttpRequest, pk: Any) -> HttpResponse:
        """Redirect GET requests to the lister dashboard."""
        return redirect("listing_mine")
