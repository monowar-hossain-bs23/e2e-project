---
unit: 001-listing-feed-query-and-consent
bolt: 009-listing-feed-query-and-consent
stage: design
status: complete
created: '2026-10-31T17:25:00Z'
---

# Technical Design: 001-listing-feed-query-and-consent

## Architecture Pattern

**Domain-Driven Read-Model & Privacy Projection Spine ([`AD-3`](file:///home/bs01496/Documents/LMS/basa-pass/docs/ARCHITECTURE-SPINE.md#L60-L75), [`AD-12`](file:///home/bs01496/Documents/LMS/basa-pass/docs/ARCHITECTURE-SPINE.md#L173-L181), [`AD-15`](file:///home/bs01496/Documents/LMS/basa-pass/docs/ARCHITECTURE-SPINE.md#L189-L197))**:
The accommodation discovery domain operates with a strict separation between mutable domain entities (`Listing`, `Passport`) and viewer-scoped read projections (`ListingProjection`).

1. **`ConsentService` (AD-3 Sole Projection Owner)**:
   - Located at `apps/passports/services/consent_service.py`.
   - Sole callable deciding what viewer $X$ can observe of listing $Y$ and lister $Z$.
   - Shields personal contact information (email and phone) unless the viewer possesses an active, verified passport (`passport.status == 'verified'`).
2. **`ListingFeedQuery` (AD-12 Sole Query Entrypoint)**:
   - Located at `apps/listings/services/feed_query.py`.
   - Sole entrypoint for any consumer querying a list of listings (feed views, detail recommendations, admin previews, sitemaps).
   - Eliminates N+1 query overhead by joining `author__user` and prefetching `photos`.
   - Automatically excludes withdrawn, archived, or stale (>60 days) posts.
3. **`CompatibilityEngine` (AD-12 Lifestyle Heuristic)**:
   - Server-side evaluator comparing seeker lifestyle preferences against listing roommate preferences across 6 canonical axes (gender, smoking, sleep, occupation, area, budget).
   - Produces an integer score $X \in [0, 6]$ without black-box machine learning or algorithmic ranking.
4. **`AuditService` Integration (AD-15 Append-Only Log)**:
   - Records every instance where a verified viewer accesses a lister's protected contact information via `action='contact_viewed'`.

---

## Layer Structure

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Presentation Layer (Intent 005 - Unit 002)                             │
│ - apps/listings/views.py (ListingFeedView, ListingDetailView)          │
│ - templates/listings/feed.html, detail.html, feed_card.html            │
├────────────────────────────────────────────────────────────────────────┤
│ Read-Model & Application Service Layer (Unit 001 - Current Bolt)       │
│ - apps/passports/services/consent_service.py (ConsentService - AD-3)   │
│ - apps/listings/services/feed_query.py (ListingFeedQuery - AD-12)      │
│ - apps/listings/services/compatibility.py (CompatibilityEngine)        │
│ - apps/audit/services/audit_service.py (AuditService - AD-15)          │
├────────────────────────────────────────────────────────────────────────┤
│ Domain Model & Value Object Layer                                      │
│ - apps/listings/models.py (Listing, ListingPhoto)                      │
│ - apps/passports/models.py (Passport, LifestyleProfile)                │
│ - apps/listings/projections.py (ListingProjection, PhotoProjection)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Component Interfaces & Data Contracts

### 1. Value Object Data Classes (`apps/listings/projections.py`)

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PhotoProjection:
    """Read-model representation of a listing photo."""

    id: UUID
    url: str
    order: int


@dataclass(frozen=True)
class ListingProjection:
    """Immutable, viewer-scoped projection of an accommodation listing."""

    id: UUID
    kind: str
    kind_display: str
    rent_bdt: int
    rent_unit: str
    rent_unit_display: str
    rent_period: str
    area: str
    body: str | None
    primary_photo_url: str | None
    photos: list[PhotoProjection] = field(default_factory=list)

    # Author metadata
    author_id: UUID | None = None
    author_display_name: str = ""
    author_tenure_display: str = ""
    author_is_verified: bool = False
    author_lifestyle_summary: str = ""

    # Soft-gated contact fields (AD-3)
    lister_email: str | None = None
    lister_phone: str | None = None
    is_contact_locked: bool = True

    # Compatibility matching (AD-12)
    compatibility_hint: int | None = None  # Integer 0 to 6
    compatibility_matches: dict[str, bool] | None = None

    created_at: datetime | None = None
    is_active: bool = True
```

---

### 2. `ConsentService` (`apps/passports/services/consent_service.py`)

```python
class ConsentService:
    """Sole owner of viewer-scoped data projection and PII redaction (AD-3)."""

    @classmethod
    def render_listing(
        cls,
        viewer: Any,
        listing: Any,
        *,
        compatibility_hint: int | None = None,
        compatibility_matches: dict[str, bool] | None = None,
    ) -> ListingProjection:
        """Transform a raw Listing ORM model into a viewer-safe ListingProjection."""
        # 1. Determine viewer verification status
        is_verified_viewer = False
        if (
            viewer
            and getattr(viewer, "is_authenticated", False)
            and hasattr(viewer, "passport")
            and getattr(viewer.passport, "is_verified", False)
        ):
            is_verified_viewer = True

        # 2. Check author tenure
        author = listing.author
        author_user = author.user
        tenure_str = author.verified_tenure_display  # e.g., "Verified for 3 months"

        # 3. Soft-gating logic
        if is_verified_viewer or (
            viewer
            and getattr(viewer, "is_authenticated", False)
            and author_user.id == getattr(viewer, "id", None)
        ):
            email = author_user.email
            phone = getattr(author_user, "phone_number", None)
            is_locked = False
        else:
            email = None
            phone = None
            is_locked = True

        # 4. Construct immutable projection
        return ListingProjection(
            id=listing.id,
            kind=listing.kind,
            kind_display=listing.get_kind_display(),
            rent_bdt=listing.rent_bdt,
            rent_unit=listing.rent_unit,
            rent_unit_display=listing.get_rent_unit_display(),
            rent_period=listing.rent_period,
            area=listing.area,
            body=listing.body,
            primary_photo_url=(
                listing.primary_photo.photo_path.url if listing.primary_photo else None
            ),
            photos=[
                PhotoProjection(id=p.id, url=p.photo_path.url, order=p.order)
                for p in listing.photos.all()
            ],
            author_id=author.id,
            author_display_name=author.display_name,
            author_tenure_display=tenure_str,
            author_is_verified=author.is_verified,
            author_lifestyle_summary=(
                author.lifestyle_summary
                if is_verified_viewer
                else "Verify to see lifestyle fit"
            ),
            lister_email=email,
            lister_phone=phone,
            is_contact_locked=is_locked,
            compatibility_hint=compatibility_hint,
            compatibility_matches=compatibility_matches,
            created_at=listing.created_at,
            is_active=listing.is_active,
        )
```

---

### 3. `CompatibilityEngine` (`apps/listings/services/compatibility.py`)

Evaluates the 6 lifestyle axes between the viewer's profile and the listing:

```python
class CompatibilityEngine:
    """Evaluates 6-axis lifestyle compatibility between seeker and listing."""

    @classmethod
    def evaluate(
        cls, seeker_profile: Any, listing: Any
    ) -> tuple[int, dict[str, bool]]:
        """Compute match status for the 6 lifestyle axes."""
        if not seeker_profile:
            return 0, {}

        # 1. Gender
        gender_match = (
            listing.pref_gender == "any"
            or listing.pref_gender == getattr(seeker_profile, "gender", None)
        )

        # 2. Smoking
        smoking_match = (
            listing.pref_smoking == "any"
            or listing.pref_smoking == getattr(seeker_profile, "smoking", None)
        )

        # 3. Sleep schedule
        sleep_match = (
            listing.pref_sleep == "flexible"
            or listing.pref_sleep == getattr(seeker_profile, "sleep_schedule", None)
        )

        # 4. Occupation
        occ_list = listing.pref_occupation or []
        occ_match = (
            "any" in occ_list
            or getattr(seeker_profile, "occupation", None) in occ_list
        )

        # 5. Area
        preferred_areas = getattr(seeker_profile, "preferred_areas", []) or []
        area_match = listing.area in preferred_areas

        # 6. Budget
        budget_bdt = getattr(seeker_profile, "budget_bdt", None)
        budget_match = budget_bdt is not None and listing.rent_bdt <= budget_bdt

        breakdown = {
            "gender": gender_match,
            "smoking": smoking_match,
            "sleep": sleep_match,
            "occupation": occ_match,
            "area": area_match,
            "budget": budget_match,
        }
        score = sum(1 for matched in breakdown.values() if matched)
        return score, breakdown
```

---

### 4. `ListingFeedQuery` (`apps/listings/services/feed_query.py`)

```python
class ListingFeedQuery:
    """Sole source of any list of accommodation listings (AD-12)."""

    PAGE_SIZE = 12

    @classmethod
    def for_viewer(
        cls,
        viewer: Any,
        *,
        areas: list[str] | None = None,
        budget_min: int | None = None,
        budget_max: int | None = None,
        kind: str | None = None,
        rent_unit: str | None = None,
        gender: str | None = None,
        smoking: str | None = None,
        sleep: str | None = None,
        occupations: list[str] | None = None,
        sort: str = "newest",
        page: int = 1,
        include_archived: bool = False,
        include_withdrawn: bool = False,
    ) -> dict[str, Any]:
        """Execute optimized ORM query, filter, sort, paginate, and project."""
        # 1. Base queryset with eager joins
        qs = Listing.objects.select_related(
            "author__user", "author__profile"
        ).prefetch_related("photos")

        # 2. Inactive / Stale exclusions
        if not include_withdrawn:
            qs = qs.filter(withdrawn_at__isnull=True)
        if not include_archived:
            qs = qs.filter(archived_at__isnull=True)
            stale_threshold = timezone.now() - timedelta(days=60)
            qs = qs.filter(created_at__gte=stale_threshold)

        # 3. Apply search filters (Additive AND)
        if areas:
            qs = qs.filter(area__in=areas)
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
            # Overlap with occupation list or 'any'
            qs = qs.filter(
                Q(pref_occupation__contains=["any"])
                | Q(pref_occupation__overlap=occupations)
            )

        # 4. Sorting
        if sort == "rent_asc":
            qs = qs.order_by("rent_bdt", "-created_at")
        elif sort == "rent_desc":
            qs = qs.order_by("-rent_bdt", "-created_at")
        else:
            qs = qs.order_by("-created_at")

        # 5. Pagination
        paginator = Paginator(qs, cls.PAGE_SIZE)
        page_obj = paginator.get_page(page)

        # 6. Extract viewer lifestyle profile for compatibility
        seeker_profile = None
        if (
            viewer
            and getattr(viewer, "is_authenticated", False)
            and hasattr(viewer, "passport")
            and getattr(viewer.passport, "is_verified", False)
            and hasattr(viewer.passport, "profile")
        ):
            seeker_profile = viewer.passport.profile

        # 7. Project listings through ConsentService
        projections = []
        for item in page_obj.object_list:
            score, matches = (
                CompatibilityEngine.evaluate(seeker_profile, item)
                if seeker_profile
                else (None, None)
            )
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
        cls, viewer: Any, listing_id: UUID
    ) -> ListingProjection | None:
        """Fetch single listing with eager loading and project with audit logging."""
        try:
            listing = (
                Listing.objects.select_related("author__user", "author__profile")
                .prefetch_related("photos")
                .get(pk=listing_id)
            )
        except Listing.DoesNotExist:
            return None

        # Exclude withdrawn / archived for public viewers unless author
        is_author = (
            viewer
            and getattr(viewer, "is_authenticated", False)
            and listing.author.user_id == getattr(viewer, "id", None)
        )
        if not is_author and (listing.is_withdrawn or listing.is_archived):
            return None

        # Compute compatibility
        seeker_profile = (
            viewer.passport.profile
            if (
                viewer
                and getattr(viewer, "is_authenticated", False)
                and hasattr(viewer, "passport")
                and getattr(viewer.passport, "is_verified", False)
                and hasattr(viewer.passport, "profile")
            )
            else None
        )
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
        """Write an append-only AuditEntry when verified seeker accesses contact info."""
        AuditService.append(
            actor=viewer,
            action="contact_viewed",
            target_id=listing.id,
            target_model="listings.Listing",
            reason="verified_viewer_reveal",
            metadata={
                "listing_id": str(listing.id),
                "author_id": str(listing.author_id),
            },
        )
```

---

## Database Indexing Optimizations

To guarantee query latency < 150ms on large catalogs, a composite index will be defined in `Listing.Meta`:

| Index Name | Fields | Rationale |
|---|---|---|
| `listing_active_feed_idx` | `["archived_at", "withdrawn_at", "-created_at"]` | Accelerates default active reverse-chronological feed sorting. |
| `listing_active_rent_idx` | `["archived_at", "withdrawn_at", "rent_bdt"]` | Accelerates price-range and rent-sorted queries. |

---

## Security & Verification Controls

1. **Server-Side PII Redaction**: Phone and email values are set to `None` in Python before crossing the boundary into Django templates. Zero reliance on CSS hiding (`d-none`).
2. **Author PII Confinement**: Citizen national identity numbers, NID scans, and selfie files are never loaded into `ListingProjection`.
3. **Audit Immutability**: All contact accesses by verified third parties write to the immutable `AuditEntry` table in the database.
