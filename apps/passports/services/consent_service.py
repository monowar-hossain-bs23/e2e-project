"""Consent and Privacy Projection Service (Architecture Spine AD-3, PRD §4.4, §4.5)."""

from typing import Any

from django.utils import timezone

from apps.listings.projections import ListingProjection, PhotoProjection


class ConsentService:
    """Sole authority governing viewer-scoped data projection and PII redaction.

    Enforces Architecture Spine AD-3: raw database models never cross into templates.
    Sensitive lister contact information (phone and email) is strictly redacted for
    unverified or anonymous viewers, and author identity files (NID, selfie, citizen ID)
    are excluded from all projections.
    """

    @classmethod
    def is_verified_viewer(cls, viewer: Any) -> bool:
        """Check whether the viewer has an active verified Tenant Passport."""
        if not viewer or not getattr(viewer, "is_authenticated", False):
            return False

        passport = getattr(viewer, "passport", None)
        if not passport:
            return False

        return bool(getattr(passport, "is_verified", False))

    @classmethod
    def compute_author_tenure(cls, author: Any) -> str:
        """Calculate human-readable verification tenure string for an author."""
        if not getattr(author, "is_verified", False):
            return "Unverified"

        # Check for verified verification attempt date
        now = timezone.now()
        verified_date = None
        if (
            hasattr(author, "_prefetched_objects_cache")
            and "verifications" in author._prefetched_objects_cache
        ):
            for v in author.verifications.all():
                if v.state == "verified" and v.reviewed_at:
                    verified_date = v.reviewed_at
                    break
        elif hasattr(author, "verifications"):
            v = author.verifications.filter(state="verified").first()
            if v and v.reviewed_at:
                verified_date = v.reviewed_at

        if not verified_date:
            verified_date = getattr(author, "created_at", now)

        delta = now - verified_date
        days = delta.days
        if days < 1:
            return "Verified today"
        if days < 30:
            return f"Verified for {days} day{'s' if days > 1 else ''}"
        months = days // 30
        if months < 12:
            return f"Verified for {months} month{'s' if months > 1 else ''}"
        years = months // 12
        return f"Verified for {years} year{'s' if years > 1 else ''}"

    @classmethod
    def extract_author_lifestyle(cls, author: Any) -> tuple[str, tuple[str, ...]]:
        """Extract lifestyle summary string and chips from author's profile."""
        profile = getattr(author, "lifestyle_profile", None)
        if not profile:
            return "Lifestyle profile not shared", ()

        chips: list[str] = []

        # Smoking
        if profile.smoking == "no":
            chips.append("Non-smoker")
        elif profile.smoking == "yes":
            chips.append("Smoker")
        elif profile.smoking == "occasionally":
            chips.append("Occasional smoker")

        # Sleep schedule
        if profile.sleep_schedule == "early_bird":
            chips.append("Early bird")
        elif profile.sleep_schedule == "night_owl":
            chips.append("Night owl")
        elif profile.sleep_schedule == "flexible":
            chips.append("Flexible schedule")

        # Occupation
        if hasattr(profile, "get_occupation_display"):
            chips.append(str(profile.get_occupation_display()))
        elif profile.occupation:
            chips.append(str(profile.occupation).replace("_", " ").title())

        summary = " · ".join(chips) if chips else "Lifestyle profile complete"
        return summary, tuple(chips)

    @classmethod
    def render_listing(
        cls,
        viewer: Any,
        listing: Any,
        *,
        compatibility_hint: int | None = None,
        compatibility_matches: dict[str, bool] | None = None,
    ) -> ListingProjection:
        """Project a Listing model into a viewer-scoped ListingProjection."""
        author = listing.author
        author_user = author.user
        viewer_is_verified = cls.is_verified_viewer(viewer)

        # Author can always view their own contact info
        viewer_is_author = (
            viewer
            and getattr(viewer, "is_authenticated", False)
            and getattr(viewer, "id", None) == author_user.id
        )

        can_view_contact = viewer_is_verified or viewer_is_author

        # Soft-gating contact channels (email & phone)
        if can_view_contact:
            email = getattr(author_user, "email", None)
            phone = getattr(author_user, "phone_number", None)
            is_locked = False
        else:
            email = None
            phone = None
            is_locked = True

        # Author tenure & lifestyle chips
        tenure = cls.compute_author_tenure(author)
        if viewer_is_verified or viewer_is_author:
            lifestyle_summary, lifestyle_chips = cls.extract_author_lifestyle(author)
        else:
            lifestyle_summary = "Verify to see lifestyle fit"
            lifestyle_chips = ()

        # Photos projection
        photos_proj: list[PhotoProjection] = []
        primary_url: str | None = None

        if hasattr(listing, "photos"):
            for photo in listing.photos.all():
                url = (
                    photo.photo_path.url
                    if hasattr(photo.photo_path, "url")
                    else str(photo.photo_path)
                )
                photos_proj.append(
                    PhotoProjection(id=photo.id, url=url, order=photo.order)
                )

        if photos_proj:
            primary_url = photos_proj[0].url
        elif listing.primary_photo:
            p = listing.primary_photo
            primary_url = (
                p.photo_path.url if hasattr(p.photo_path, "url") else str(p.photo_path)
            )

        pref_occ = (
            tuple(listing.pref_occupation)
            if isinstance(listing.pref_occupation, list)
            else ()
        )

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
            primary_photo_url=primary_url,
            photos=tuple(photos_proj),
            author_id=author.id,
            author_display_name=author.display_name,
            author_tenure_display=tenure,
            author_is_verified=author.is_verified,
            author_lifestyle_summary=lifestyle_summary,
            author_lifestyle_chips=lifestyle_chips,
            pref_gender=listing.pref_gender,
            pref_gender_display=listing.get_pref_gender_display(),
            pref_smoking=listing.pref_smoking,
            pref_smoking_display=listing.get_pref_smoking_display(),
            pref_sleep=listing.pref_sleep,
            pref_sleep_display=listing.get_pref_sleep_display(),
            pref_occupations=pref_occ,
            lister_email=email,
            lister_phone=phone,
            is_contact_locked=is_locked,
            compatibility_hint=compatibility_hint,
            compatibility_matches=compatibility_matches,
            created_at=listing.created_at,
            is_active=listing.is_active,
        )
