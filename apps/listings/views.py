"""Views for listing authoring, management, and discovery (Story 020–028)."""

from typing import Any

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView, UpdateView, View

from apps.listings.constants import (
    MAX_ACTIVE_LISTINGS_PER_USER,
    ListingKind,
    PreferredGender,
    PreferredOccupation,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentUnit,
)
from apps.listings.forms import ListingCreationForm, ListingEditForm
from apps.listings.mixins import VerifiedTenantRequiredMixin
from apps.listings.models import Listing
from apps.listings.services.feed_query import ListingFeedQuery
from apps.listings.services.listing_service import ListingService
from apps.passports.validators import DHAKA_SUB_AREAS


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

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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
        phone_number = form.cleaned_data["phone_number"]

        # Persist contact phone number to author user account
        if self.request.user.phone_number != phone_number:
            self.request.user.phone_number = phone_number
            self.request.user.save(update_fields=["phone_number", "updated_at"])

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
        phone_number = form.cleaned_data["phone_number"]

        # Persist contact phone number to author user account
        author_user = listing.author.user
        if author_user.phone_number != phone_number:
            author_user.phone_number = phone_number
            author_user.save(update_fields=["phone_number", "updated_at"])

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


class ListingFeedView(TemplateView):
    """Public accommodation discovery feed with multi-axis filtering and sorting."""

    template_name = "listings/feed.html"

    def get_template_names(self) -> list[str]:
        if self.request.headers.get("HX-Request") == "true":
            return ["listings/partials/feed_results.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        req = self.request.GET

        # Multi-value area filter (support ?area=Mirpur or ?areas=Mirpur)
        areas = req.getlist("area") or req.getlist("areas") or []
        if not areas and req.get("area"):
            areas = [req.get("area")]
        clean_areas = [a for a in areas if a]

        # Budget filters
        budget_min_raw = req.get("budget_min")
        budget_max_raw = req.get("budget_max")
        budget_min: int | None = None
        budget_max: int | None = None
        if budget_min_raw and budget_min_raw.isdigit():
            budget_min = int(budget_min_raw)
        if budget_max_raw and budget_max_raw.isdigit():
            budget_max = int(budget_max_raw)

        # Kind & rent unit
        kind = req.get("kind") or None
        rent_unit = req.get("rent_unit") or None

        # Lifestyle preferences
        gender = req.get("gender") or None
        smoking = req.get("smoking") or None
        sleep = req.get("sleep") or None
        occupations = req.getlist("occupation") or req.getlist("occupations") or []
        if not occupations and req.get("occupation"):
            occupations = [req.get("occupation")]
        clean_occupations = [o for o in occupations if o]

        # Sorting
        sort = req.get("sort", "newest")
        if sort not in ("newest", "rent_asc", "rent_desc"):
            sort = "newest"

        # Pagination
        page_raw = req.get("page", "1")
        page = int(page_raw) if page_raw.isdigit() else 1

        # Calculate active filters count for badge pill
        active_filter_count = 0
        if clean_areas:
            active_filter_count += len(clean_areas)
        if budget_min is not None and budget_min > 500:
            active_filter_count += 1
        if budget_max is not None and budget_max < 50000:
            active_filter_count += 1
        if kind:
            active_filter_count += 1
        if rent_unit:
            active_filter_count += 1
        if gender and gender != "any":
            active_filter_count += 1
        if smoking and smoking != "any":
            active_filter_count += 1
        if sleep and sleep != "flexible":
            active_filter_count += 1
        if clean_occupations and "any" not in clean_occupations:
            active_filter_count += len(clean_occupations)

        # Execute query
        feed_data = ListingFeedQuery.for_viewer(
            viewer=self.request.user,
            areas=clean_areas or None,
            budget_min=budget_min,
            budget_max=budget_max,
            kind=kind,
            rent_unit=rent_unit,
            gender=gender,
            smoking=smoking,
            sleep=sleep,
            occupations=clean_occupations or None,
            sort=sort,
            page=page,
        )

        context.update(
            {
                "projections": feed_data["projections"],
                "page_obj": feed_data["page_obj"],
                "paginator": feed_data["paginator"],
                "total_count": feed_data["total_count"],
                "active_filter_count": active_filter_count,
                "current_sort": sort,
                # Current filter state for inputs
                "selected_areas": clean_areas,
                "selected_budget_min": budget_min if budget_min is not None else 500,
                "selected_budget_max": budget_max if budget_max is not None else 50000,
                "selected_kind": kind or "",
                "selected_rent_unit": rent_unit or "",
                "selected_gender": gender or "any",
                "selected_smoking": smoking or "any",
                "selected_sleep": sleep or "flexible",
                "selected_occupations": clean_occupations,
                # Choices & Constants
                "dhaka_sub_areas": DHAKA_SUB_AREAS,
                "listing_kinds": ListingKind.choices,
                "rent_units": RentUnit.choices,
                "gender_choices": PreferredGender.choices,
                "smoking_choices": PreferredSmoking.choices,
                "sleep_choices": PreferredSleepSchedule.choices,
                "occupation_choices": PreferredOccupation.choices,
            }
        )
        return context


class ListingDetailView(TemplateView):
    """Public detail page for an accommodation listing (Story 028).

    Guarantees soft-gated contact shielding via ConsentService and emits
    an append-only AuditEntry when a verified seeker accesses contact info.
    """

    template_name = "listings/detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        pk = kwargs.get("pk")
        proj = ListingFeedQuery.get_detail_for_viewer(
            viewer=self.request.user,
            listing_id=pk,
        )
        if proj is None:
            raise Http404(_("Listing not found or no longer active."))

        is_author = (
            self.request.user.is_authenticated
            and hasattr(self.request.user, "passport")
            and proj.author_id == self.request.user.passport.id
        )

        context["listing"] = proj
        context["is_author"] = is_author
        return context
