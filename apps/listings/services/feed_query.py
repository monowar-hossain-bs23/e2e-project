"""Unified read-model query engine for Accommodation Listings (PRD §4.4, AD-12)."""

from datetime import timedelta
from typing import Any
from uuid import UUID

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from apps.audit.services.audit_service import AuditService
from apps.listings.models import Listing
from apps.listings.projections import ListingProjection
from apps.listings.services.compatibility import CompatibilityEngine
from apps.passports.services.consent_service import ConsentService


class ListingFeedQuery:
    """Sole source of any list of accommodation listings (AD-12).

    Guarantees active inventory invariants (excluding withdrawn, archived, or
    >60d stale listings), eliminates N+1 query loops via eager joins, calculates
    transparent 6-axis compatibility scores, and applies viewer-scoped PII shielding
    through ConsentService.
    """

    PAGE_SIZE: int = 12
    AUTO_ARCHIVE_DAYS: int = 60

    @classmethod
    def for_viewer(
        cls,
        viewer: Any,
        *,
        areas: list[str] | str | None = None,
        budget_min: int | None = None,
        budget_max: int | None = None,
        kind: str | None = None,
        rent_unit: str | None = None,
        gender: str | None = None,
        smoking: str | None = None,
        sleep: str | None = None,
        occupations: list[str] | str | None = None,
        sort: str = "newest",
        page: int = 1,
        page_size: int = PAGE_SIZE,
        include_archived: bool = False,
        include_withdrawn: bool = False,
    ) -> dict[str, Any]:
        """Execute optimized ORM query, filter, sort, paginate, and project.

        Returns a dictionary containing:
            - 'projections': list[ListingProjection]
            - 'paginator': Paginator
            - 'page_obj': Page
            - 'total_count': int
        """
        # 1. Base queryset with eager joins eliminating N+1 queries
        qs = Listing.objects.select_related(
            "author__user",
            "author__lifestyle_profile",
        ).prefetch_related("photos", "author__verifications")

        # 2. Lifecycle status filtering
        if not include_withdrawn:
            qs = qs.filter(withdrawn_at__isnull=True)

        if not include_archived:
            qs = qs.filter(archived_at__isnull=True)
            stale_threshold = timezone.now() - timedelta(days=cls.AUTO_ARCHIVE_DAYS)
            qs = qs.filter(created_at__gte=stale_threshold)

        # 3. Additive filters
        if areas:
            if isinstance(areas, str):
                qs = qs.filter(area=areas)
            elif isinstance(areas, list | tuple | set):
                clean_areas = [a for a in areas if a]
                if clean_areas:
                    qs = qs.filter(area__in=clean_areas)

        if budget_min is not None:
            qs = qs.filter(rent_bdt__gte=budget_min)

        if budget_max is not None:
            qs = qs.filter(rent_bdt__lte=budget_max)

        if kind:
            qs = qs.filter(kind=kind)

        if rent_unit:
            qs = qs.filter(rent_unit=rent_unit)

        if gender and gender != "any":
            qs = qs.filter(Q(pref_gender="any") | Q(pref_gender=gender))

        if smoking and smoking != "any":
            qs = qs.filter(Q(pref_smoking="any") | Q(pref_smoking=smoking))

        if sleep and sleep != "flexible":
            qs = qs.filter(Q(pref_sleep="flexible") | Q(pref_sleep=sleep))

        if occupations:
            occ_list = (
                [occupations] if isinstance(occupations, str) else list(occupations)
            )
            clean_occs = [o for o in occ_list if o]
            if clean_occs:
                q_occ = Q(pref_occupation__icontains='"any"')
                for occ in clean_occs:
                    q_occ |= Q(pref_occupation__icontains=f'"{occ}"')
                qs = qs.filter(q_occ)

        # 4. Sorting
        if sort == "rent_asc":
            qs = qs.order_by("rent_bdt", "-created_at")
        elif sort == "rent_desc":
            qs = qs.order_by("-rent_bdt", "-created_at")
        else:
            qs = qs.order_by("-created_at")

        # 5. Pagination
        paginator = Paginator(qs, page_size)
        page_obj = paginator.get_page(page)

        # 6. Seeker lifestyle profile for compatibility
        seeker_profile = None
        if (
            viewer
            and getattr(viewer, "is_authenticated", False)
            and hasattr(viewer, "passport")
            and getattr(viewer.passport, "is_verified", False)
            and hasattr(viewer.passport, "lifestyle_profile")
        ):
            seeker_profile = viewer.passport.lifestyle_profile

        # 7. Project listings
        projections = []
        for item in page_obj.object_list:
            if seeker_profile:
                score, matches = CompatibilityEngine.evaluate(seeker_profile, item)
            else:
                score, matches = None, None

            proj = ConsentService.render_listing(
                viewer=viewer,
                listing=item,
                compatibility_hint=score,
                compatibility_matches=matches,
            )
            projections.append(proj)

        return {
            "projections": projections,
            "page_obj": page_obj,
            "paginator": paginator,
            "total_count": paginator.count,
        }

    @classmethod
    def get_detail_for_viewer(
        cls, viewer: Any, listing_id: UUID | str
    ) -> ListingProjection | None:
        """Fetch single listing with eager loading and project with audit logging."""
        try:
            listing = (
                Listing.objects.select_related(
                    "author__user", "author__lifestyle_profile"
                )
                .prefetch_related("photos", "author__verifications")
                .get(pk=listing_id)
            )
        except (Listing.DoesNotExist, ValueError):
            return None

        # Exclude withdrawn / archived for public viewers unless author
        is_author = bool(
            viewer
            and getattr(viewer, "is_authenticated", False)
            and listing.author.user_id == getattr(viewer, "id", None)
        )
        if not is_author and (listing.is_withdrawn or listing.is_archived):
            return None

        # Compatibility computation
        seeker_profile = None
        if (
            viewer
            and getattr(viewer, "is_authenticated", False)
            and hasattr(viewer, "passport")
            and getattr(viewer.passport, "is_verified", False)
            and hasattr(viewer.passport, "lifestyle_profile")
        ):
            seeker_profile = viewer.passport.lifestyle_profile

        score, matches = (
            CompatibilityEngine.evaluate(seeker_profile, listing)
            if seeker_profile
            else (None, None)
        )

        proj = ConsentService.render_listing(
            viewer=viewer,
            listing=listing,
            compatibility_hint=score,
            compatibility_matches=matches,
        )

        # Audit logging on contact disclosure for non-authors (AD-15)
        if (
            not is_author
            and not proj.is_contact_locked
            and viewer
            and getattr(viewer, "is_authenticated", False)
        ):
            cls.record_contact_reveal(viewer=viewer, listing=listing)

        return proj

    @classmethod
    def record_contact_reveal(cls, *, viewer: Any, listing: Any) -> None:
        """Write append-only AuditEntry when verified seeker accesses contact."""
        AuditService.append(
            actor_id=viewer.id,
            target=listing,
            action="contact_viewed",
            reason_code="verified_viewer_reveal",
            after_state={"author_passport_id": str(listing.author_id)},
        )
