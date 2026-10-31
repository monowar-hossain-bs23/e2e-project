"""Management command to auto-archive stale listings older than 60 days.

Governed by FR-12 and Architecture Spine AD-6.
"""

from typing import Any

from django.core.management.base import BaseCommand

from apps.listings.constants import AUTO_ARCHIVE_DAYS
from apps.listings.services.listing_service import ListingService


class Command(BaseCommand):
    """Archive active listings that have exceeded the 60-day lifecycle window."""

    help = "Auto-archive active listings older than 60 days."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--days",
            type=int,
            default=AUTO_ARCHIVE_DAYS,
            help=(
                "Number of days after creation to archive active listings "
                f"(default: {AUTO_ARCHIVE_DAYS})."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        days = options["days"]
        res = ListingService.archive_stale(cutoff_days=days)
        count = res.get("archived_count", 0)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully archived {count} listing(s) older than {days} days."
            )
        )
