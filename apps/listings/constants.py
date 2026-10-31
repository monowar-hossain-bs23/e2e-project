"""Constants, enums, and choices for Accommodation Listings (PRD §4.4, AD-6)."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class ListingKind(models.TextChoices):
    """Accommodation kind."""

    SEAT = "seat", _("Seat")
    ROOM = "room", _("Room")


class RentUnit(models.TextChoices):
    """Rent pricing denominator."""

    PER_SEAT = "per_seat", _("Per Seat")
    PER_ROOM = "per_room", _("Per Room")


class RentPeriod(models.TextChoices):
    """Rent billing period (fixed to per_month in v1)."""

    PER_MONTH = "per_month", _("Per Month")


class PreferredGender(models.TextChoices):
    """Preferred roommate gender."""

    MALE = "male", _("Male")
    FEMALE = "female", _("Female")
    ANY = "any", _("Any")


class PreferredSmoking(models.TextChoices):
    """Preferred roommate smoking habit."""

    YES = "yes", _("Yes")
    NO = "no", _("No")
    ANY = "any", _("Any")


class PreferredSleepSchedule(models.TextChoices):
    """Preferred roommate sleep schedule."""

    EARLY_BIRD = "early_bird", _("Early Bird")
    NIGHT_OWL = "night_owl", _("Night Owl")
    FLEXIBLE = "flexible", _("Flexible")


class PreferredOccupation(models.TextChoices):
    """Preferred roommate occupations."""

    STUDENT = "student", _("Student")
    GARMENTS_WORKER = "garments_worker", _("Garments Worker")
    PRIVATE_JOB = "private_job", _("Private Job")
    FREELANCER = "freelancer", _("Freelancer")
    OTHER = "other", _("Other")
    ANY = "any", _("Any")


MIN_RENT_BDT: int = 500
MAX_RENT_BDT: int = 50000
MIN_LISTING_PHOTOS: int = 1
MAX_LISTING_PHOTOS: int = 7
MAX_PHOTO_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
MAX_ACTIVE_LISTINGS_PER_USER: int = 3
AUTO_ARCHIVE_DAYS: int = 60
MAX_BODY_LENGTH: int = 500
