"""Django Admin configuration for Accommodation Listings (AD-6, AD-10)."""

from django.contrib import admin
from django.utils.html import format_html

from apps.listings.models import Listing, ListingPhoto


class ListingPhotoInline(admin.TabularInline):
    """Inline view of photos attached to a listing."""

    model = ListingPhoto
    extra = 0
    readonly_fields = ("id", "photo_thumbnail", "order", "created_at")
    fields = ("photo_thumbnail", "order", "created_at")

    @admin.display(description="Preview")
    def photo_thumbnail(self, obj: ListingPhoto) -> str:
        if not obj.photo_path:
            return "-"
        return format_html(
            '<img src="/media/{0}" style="max-height: 80px; max-width: 120px; '
            'border-radius: 4px; border: 1px solid #E2E8F0;" />',
            obj.photo_path,
        )


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    """Admin configuration for Listing aggregate root."""

    list_display = (
        "id_short",
        "author_display_name",
        "kind_badge",
        "rent_display",
        "areas_display",
        "status_badge",
        "created_at",
    )
    list_filter = ("kind", "rent_unit", "created_at", "archived_at", "withdrawn_at")
    search_fields = ("author__display_name", "author__user__email", "body")
    readonly_fields = (
        "id",
        "author",
        "kind",
        "rent_period",
        "area",
        "created_at",
        "updated_at",
        "archived_at",
        "withdrawn_at",
    )
    inlines = [ListingPhotoInline]

    @admin.display(description="ID")
    def id_short(self, obj: Listing) -> str:
        return str(obj.id)[:8]

    @admin.display(description="Author")
    def author_display_name(self, obj: Listing) -> str:
        return obj.author.display_name

    @admin.display(description="Kind")
    def kind_badge(self, obj: Listing) -> str:
        color = "#0F6E7A" if obj.kind == "room" else "#C56B4F"
        return format_html(
            '<span style="background-color: {0}; color: white; padding: 2px 7px; '
            'border-radius: 10px; font-weight: 600; font-size: 11px;">{1}</span>',
            color,
            obj.get_kind_display(),
        )

    @admin.display(description="Rent")
    def rent_display(self, obj: Listing) -> str:
        return f"৳{obj.rent_bdt:,}/{obj.get_rent_unit_display()}"

    @admin.display(description="Area")
    def areas_display(self, obj: Listing) -> str:
        return obj.area or "-"

    @admin.display(description="Status")
    def status_badge(self, obj: Listing) -> str:
        if obj.is_withdrawn:
            color = "#64748B"
            label = "Withdrawn"
        elif obj.is_archived:
            color = "#B45309"
            label = "Archived"
        else:
            color = "#16A34A"
            label = "Active"

        return format_html(
            '<span style="background-color: {0}; color: white; padding: 2px 7px; '
            'border-radius: 10px; font-weight: 600; font-size: 11px;">{1}</span>',
            color,
            label,
        )


@admin.register(ListingPhoto)
class ListingPhotoAdmin(admin.ModelAdmin):
    """Admin configuration for standalone ListingPhoto queries."""

    list_display = ("id", "listing_link", "order", "created_at")
    readonly_fields = ("id", "listing", "photo_path", "order", "created_at")

    @admin.display(description="Listing")
    def listing_link(self, obj: ListingPhoto) -> str:
        return str(obj.listing)
