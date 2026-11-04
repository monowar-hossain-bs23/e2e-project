"""Django management command for seeding development and testing data.

Populates realistic dummy data including admin, staff reviewer, verified tenants,
pending verification queue, rejected attempts, lifestyle profiles, and listings.
"""

import hashlib
from datetime import timedelta
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import EmailVerificationToken, User
from apps.audit.models import AuditEntry
from apps.listings.constants import (
    ListingKind,
    PreferredGender,
    PreferredOccupation,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentUnit,
)
from apps.listings.models import Listing, ListingPhoto
from apps.passports.models import LifestyleProfile, Passport
from apps.verification.models import Verification
from apps.verification.services.reject_reasons import RejectReason

# Minimal valid 16x16 JPEG bytes for mock photo placeholders
MINIMAL_JPEG_BYTES: bytes = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\xff\xc0\x00\x0b\x08\x00\x10\x00\x10\x01\x01\x11\x00"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)


class Command(BaseCommand):
    """Seed database with realistic initial testing data."""

    help = "Seeds database with demo accounts, passports, and listings."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing seeded records before populating.",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="pass123456",
            help="Default password for seeded user accounts (default: 'pass123456').",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        clear: bool = options["clear"]
        default_pwd: str = options["password"]

        self.stdout.write(self.style.NOTICE("🌱 Starting database seeding..."))

        if clear:
            self._clear_data()

        self._ensure_sample_media_files()

        with transaction.atomic():
            stats = self._seed_data(default_pwd)

        self.stdout.write(
            self.style.SUCCESS("\n✅ Database seeding successfully completed!")
        )
        self._print_summary(stats, default_pwd)

    def _clear_data(self) -> None:
        """Wipe existing application entities in dependency order."""
        self.stdout.write(self.style.WARNING("Clearing existing data..."))
        ListingPhoto.objects.all().delete()
        Listing.objects.all().delete()
        Verification.objects.all().delete()
        LifestyleProfile.objects.all().delete()
        Passport.objects.all().delete()
        EmailVerificationToken.objects.all().delete()
        User.objects.all().delete()
        AuditEntry.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Existing data cleared."))

    def _ensure_sample_media_files(self) -> None:
        """Create sample mock images on disk for photo and verification lookups."""
        media_root = Path(getattr(settings, "MEDIA_ROOT", settings.BASE_DIR / "media"))
        sample_dir = media_root / "listings" / "photos" / "sample"
        sample_dir.mkdir(parents=True, exist_ok=True)

        for filename in ("sample_room.jpg", "sample_seat.jpg"):
            target_path = sample_dir / filename
            if not target_path.exists():
                target_path.write_bytes(MINIMAL_JPEG_BYTES)

        private_root = Path(
            getattr(settings, "MEDIA_PRIVATE_ROOT", settings.BASE_DIR / "media_private")
        )
        private_sample_dir = private_root / "sample"
        private_sample_dir.mkdir(parents=True, exist_ok=True)

        for filename in ("nid_front.jpg", "nid_back.jpg", "selfie.jpg"):
            target_path = private_sample_dir / filename
            if not target_path.exists():
                target_path.write_bytes(MINIMAL_JPEG_BYTES)

    def _seed_data(self, default_pwd: str) -> dict[str, int]:
        """Create and populate all demo users, profiles, and listings."""
        now = timezone.now()
        stats = {
            "users": 0,
            "passports": 0,
            "verifications": 0,
            "listings": 0,
            "photos": 0,
        }

        # 1. Superuser / Admin
        admin_email = "admin@bashapass.com"
        admin_user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                "display_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
                "email_verified": True,
                "phone_number": "+8801700000001",
            },
        )
        if created:
            admin_user.set_password("admin123456")
            admin_user.save()
            stats["users"] += 1

        # 2. Staff Reviewer
        reviewer_email = "reviewer@bashapass.com"
        reviewer_user, created = User.objects.get_or_create(
            email=reviewer_email,
            defaults={
                "display_name": "Staff Reviewer",
                "is_staff": True,
                "is_superuser": False,
                "email_verified": True,
                "phone_number": "+8801700000002",
            },
        )
        if created:
            reviewer_user.set_password("reviewer123456")
            reviewer_user.save()
            stats["users"] += 1

        # 3. Verified Users with Passports & Listings
        verified_fixtures = [
            {
                "email": "tanvir@example.com",
                "display_name": "Tanvir Ahmed",
                "passport_handle": "tanvir_ahmed",
                "phone": "+8801711112222",
                "lifestyle": {
                    "gender": LifestyleProfile.Gender.MALE,
                    "occupation": LifestyleProfile.Occupation.STUDENT,
                    "smoking": LifestyleProfile.Smoking.NO,
                    "sleep_schedule": LifestyleProfile.SleepSchedule.EARLY_BIRD,
                    "area_preference": ["Dhanmondi", "Mirpur"],
                    "budget_min": 5000,
                    "budget_max": 15000,
                },
                "listings": [
                    {
                        "kind": ListingKind.ROOM,
                        "rent_unit": RentUnit.PER_ROOM,
                        "rent_bdt": 12000,
                        "area": "Dhanmondi",
                        "body": (
                            "Master bed with attached washroom in a 3BHK flat "
                            "near Dhanmondi 27. Quiet and hygienic roommate."
                        ),
                        "pref_gender": PreferredGender.MALE,
                        "pref_smoking": PreferredSmoking.NO,
                        "pref_sleep": PreferredSleepSchedule.EARLY_BIRD,
                        "pref_occupation": [
                            PreferredOccupation.STUDENT,
                            PreferredOccupation.PRIVATE_JOB,
                        ],
                        "photo": "listings/photos/sample/sample_room.jpg",
                    },
                    {
                        "kind": ListingKind.SEAT,
                        "rent_unit": RentUnit.PER_SEAT,
                        "rent_bdt": 5500,
                        "area": "Mirpur",
                        "body": (
                            "Single seat in a 2-bed room. 5 min walk from "
                            "Mirpur 10 Metro. Utilities and wifi included."
                        ),
                        "pref_gender": PreferredGender.MALE,
                        "pref_smoking": PreferredSmoking.NO,
                        "pref_sleep": PreferredSleepSchedule.FLEXIBLE,
                        "pref_occupation": [PreferredOccupation.STUDENT],
                        "photo": "listings/photos/sample/sample_seat.jpg",
                    },
                ],
            },
            {
                "email": "nusrat@example.com",
                "display_name": "Nusrat Jahan",
                "passport_handle": "nusrat_jahan",
                "phone": "+8801811113333",
                "lifestyle": {
                    "gender": LifestyleProfile.Gender.FEMALE,
                    "occupation": LifestyleProfile.Occupation.PRIVATE_JOB,
                    "smoking": LifestyleProfile.Smoking.NO,
                    "sleep_schedule": LifestyleProfile.SleepSchedule.FLEXIBLE,
                    "area_preference": ["Banani", "Gulshan", "Mohammadpur"],
                    "budget_min": 10000,
                    "budget_max": 25000,
                },
                "listings": [
                    {
                        "kind": ListingKind.ROOM,
                        "rent_unit": RentUnit.PER_ROOM,
                        "rent_bdt": 18500,
                        "area": "Banani",
                        "body": (
                            "Private room with AC and bath in Banani Block D. "
                            "24/7 security and generator. Female tenants only."
                        ),
                        "pref_gender": PreferredGender.FEMALE,
                        "pref_smoking": PreferredSmoking.NO,
                        "pref_sleep": PreferredSleepSchedule.FLEXIBLE,
                        "pref_occupation": [
                            PreferredOccupation.PRIVATE_JOB,
                            PreferredOccupation.FREELANCER,
                        ],
                        "photo": "listings/photos/sample/sample_room.jpg",
                    },
                    {
                        "kind": ListingKind.SEAT,
                        "rent_unit": RentUnit.PER_SEAT,
                        "rent_bdt": 6500,
                        "area": "Mohammadpur",
                        "body": (
                            "One seat available in Japan Garden City. "
                            "Calm environment for female students or jobs."
                        ),
                        "pref_gender": PreferredGender.FEMALE,
                        "pref_smoking": PreferredSmoking.NO,
                        "pref_sleep": PreferredSleepSchedule.EARLY_BIRD,
                        "pref_occupation": [
                            PreferredOccupation.STUDENT,
                            PreferredOccupation.PRIVATE_JOB,
                        ],
                        "photo": "listings/photos/sample/sample_seat.jpg",
                    },
                ],
            },
            {
                "email": "sakib@example.com",
                "display_name": "Sakib Hasan",
                "passport_handle": "sakib_hasan",
                "phone": "+8801911114444",
                "lifestyle": {
                    "gender": LifestyleProfile.Gender.MALE,
                    "occupation": LifestyleProfile.Occupation.FREELANCER,
                    "smoking": LifestyleProfile.Smoking.OCCASIONALLY,
                    "sleep_schedule": LifestyleProfile.SleepSchedule.NIGHT_OWL,
                    "area_preference": ["Bashundhara", "Uttara"],
                    "budget_min": 8000,
                    "budget_max": 22000,
                },
                "listings": [
                    {
                        "kind": ListingKind.ROOM,
                        "rent_unit": RentUnit.PER_ROOM,
                        "rent_bdt": 14000,
                        "area": "Bashundhara",
                        "body": (
                            "Airy room in Bashundhara Block C. Fast fiber "
                            "broadband. Remote workers welcome."
                        ),
                        "pref_gender": PreferredGender.ANY,
                        "pref_smoking": PreferredSmoking.ANY,
                        "pref_sleep": PreferredSleepSchedule.NIGHT_OWL,
                        "pref_occupation": [
                            PreferredOccupation.FREELANCER,
                            PreferredOccupation.PRIVATE_JOB,
                        ],
                        "photo": "listings/photos/sample/sample_room.jpg",
                    },
                    {
                        "kind": ListingKind.SEAT,
                        "rent_unit": RentUnit.PER_SEAT,
                        "rent_bdt": 4800,
                        "area": "Uttara",
                        "body": "Seat filled, listing withdrawn by owner.",
                        "pref_gender": PreferredGender.MALE,
                        "pref_smoking": PreferredSmoking.NO,
                        "pref_sleep": PreferredSleepSchedule.FLEXIBLE,
                        "pref_occupation": [PreferredOccupation.ANY],
                        "withdrawn": True,
                        "photo": "listings/photos/sample/sample_seat.jpg",
                    },
                    {
                        "kind": ListingKind.ROOM,
                        "rent_unit": RentUnit.PER_ROOM,
                        "rent_bdt": 11000,
                        "area": "Uttara",
                        "body": "Older listing auto-archived after 60-day window.",
                        "pref_gender": PreferredGender.ANY,
                        "pref_smoking": PreferredSmoking.ANY,
                        "pref_sleep": PreferredSleepSchedule.FLEXIBLE,
                        "pref_occupation": [PreferredOccupation.ANY],
                        "archived": True,
                        "photo": "listings/photos/sample/sample_room.jpg",
                    },
                ],
            },
            {
                "email": "rahim@example.com",
                "display_name": "Rahim Mia",
                "passport_handle": "rahim_mia",
                "phone": "+8801611115555",
                "lifestyle": {
                    "gender": LifestyleProfile.Gender.MALE,
                    "occupation": LifestyleProfile.Occupation.GARMENTS_WORKER,
                    "smoking": LifestyleProfile.Smoking.NO,
                    "sleep_schedule": LifestyleProfile.SleepSchedule.EARLY_BIRD,
                    "area_preference": ["Gazipur", "Mirpur", "Tejgaon"],
                    "budget_min": 2000,
                    "budget_max": 6000,
                },
                "listings": [
                    {
                        "kind": ListingKind.SEAT,
                        "rent_unit": RentUnit.PER_SEAT,
                        "rent_bdt": 3200,
                        "area": "Gazipur",
                        "body": (
                            "Affordable mess seat near industrial hub. Clean "
                            "water and peaceful shared amenities."
                        ),
                        "pref_gender": PreferredGender.MALE,
                        "pref_smoking": PreferredSmoking.NO,
                        "pref_sleep": PreferredSleepSchedule.EARLY_BIRD,
                        "pref_occupation": [
                            PreferredOccupation.GARMENTS_WORKER,
                            PreferredOccupation.OTHER,
                        ],
                        "photo": "listings/photos/sample/sample_seat.jpg",
                    },
                ],
            },
            {
                "email": "farhana@example.com",
                "display_name": "Farhana Akter",
                "passport_handle": "farhana_akter",
                "phone": "+8801511116666",
                "lifestyle": {
                    "gender": LifestyleProfile.Gender.FEMALE,
                    "occupation": LifestyleProfile.Occupation.STUDENT,
                    "smoking": LifestyleProfile.Smoking.NO,
                    "sleep_schedule": LifestyleProfile.SleepSchedule.EARLY_BIRD,
                    "area_preference": ["Dhanmondi", "Ramna"],
                    "budget_min": 4000,
                    "budget_max": 12000,
                },
                "listings": [
                    {
                        "kind": ListingKind.SEAT,
                        "rent_unit": RentUnit.PER_SEAT,
                        "rent_bdt": 4800,
                        "area": "Ramna",
                        "body": (
                            "Female student seat in Siddheshwari near varsity. "
                            "Safe mess with guard security."
                        ),
                        "pref_gender": PreferredGender.FEMALE,
                        "pref_smoking": PreferredSmoking.NO,
                        "pref_sleep": PreferredSleepSchedule.EARLY_BIRD,
                        "pref_occupation": [PreferredOccupation.STUDENT],
                        "photo": "listings/photos/sample/sample_seat.jpg",
                    },
                    {
                        "kind": ListingKind.ROOM,
                        "rent_unit": RentUnit.PER_ROOM,
                        "rent_bdt": 9500,
                        "area": "Dhanmondi",
                        "body": (
                            "Small quiet room in Dhanmondi 9A. "
                            "Ideal for female student studying."
                        ),
                        "pref_gender": PreferredGender.FEMALE,
                        "pref_smoking": PreferredSmoking.NO,
                        "pref_sleep": PreferredSleepSchedule.EARLY_BIRD,
                        "pref_occupation": [PreferredOccupation.STUDENT],
                        "photo": "listings/photos/sample/sample_room.jpg",
                    },
                ],
            },
            {
                "email": "asif@example.com",
                "display_name": "Asif Mahmud",
                "passport_handle": "asif_mahmud",
                "phone": "+8801711117777",
                "lifestyle": {
                    "gender": LifestyleProfile.Gender.MALE,
                    "occupation": LifestyleProfile.Occupation.PRIVATE_JOB,
                    "smoking": LifestyleProfile.Smoking.NO,
                    "sleep_schedule": LifestyleProfile.SleepSchedule.FLEXIBLE,
                    "area_preference": ["Baridhara", "Gulshan"],
                    "budget_min": 15000,
                    "budget_max": 35000,
                },
                "listings": [
                    {
                        "kind": ListingKind.ROOM,
                        "rent_unit": RentUnit.PER_ROOM,
                        "rent_bdt": 24000,
                        "area": "Baridhara",
                        "body": (
                            "Executive bedroom in Baridhara J Block with AC, "
                            "lift, and parking. Working professional."
                        ),
                        "pref_gender": PreferredGender.MALE,
                        "pref_smoking": PreferredSmoking.NO,
                        "pref_sleep": PreferredSleepSchedule.FLEXIBLE,
                        "pref_occupation": [PreferredOccupation.PRIVATE_JOB],
                        "photo": "listings/photos/sample/sample_room.jpg",
                    },
                ],
            },
        ]

        for fix in verified_fixtures:
            user, u_created = User.objects.get_or_create(
                email=fix["email"],
                defaults={
                    "display_name": fix["display_name"],
                    "email_verified": True,
                    "phone_number": fix["phone"],
                },
            )
            if u_created:
                user.set_password(default_pwd)
                user.save()
                stats["users"] += 1

            passport, p_created = Passport.objects.get_or_create(
                user=user,
                defaults={
                    "display_name": fix["passport_handle"],
                    "status": Passport.Status.VERIFIED,
                },
            )
            if p_created:
                stats["passports"] += 1

            Verification.objects.get_or_create(
                passport=passport,
                state=Verification.State.VERIFIED,
                defaults={
                    "nid_front_path": "sample/nid_front.jpg",
                    "nid_back_path": "sample/nid_back.jpg",
                    "selfie_path": "sample/selfie.jpg",
                    "submitted_at": now - timedelta(days=10),
                    "reviewed_by": reviewer_user,
                    "reviewed_at": now - timedelta(days=9),
                    "reviewer_notes": "Identity documentation verified and clear.",
                },
            )
            stats["verifications"] += 1

            ls = fix["lifestyle"]
            LifestyleProfile.objects.get_or_create(
                passport=passport,
                defaults={
                    "gender": ls["gender"],
                    "occupation": ls["occupation"],
                    "smoking": ls["smoking"],
                    "sleep_schedule": ls["sleep_schedule"],
                    "area_preference": ls["area_preference"],
                    "budget_min": ls["budget_min"],
                    "budget_max": ls["budget_max"],
                },
            )

            for l_data in fix["listings"]:
                listing, l_created = Listing.objects.get_or_create(
                    author=passport,
                    area=l_data["area"],
                    rent_bdt=l_data["rent_bdt"],
                    kind=l_data["kind"],
                    defaults={
                        "rent_unit": l_data["rent_unit"],
                        "body": l_data["body"],
                        "pref_gender": l_data["pref_gender"],
                        "pref_smoking": l_data["pref_smoking"],
                        "pref_sleep": l_data["pref_sleep"],
                        "pref_occupation": l_data["pref_occupation"],
                        "withdrawn_at": (
                            now - timedelta(days=2) if l_data.get("withdrawn") else None
                        ),
                        "archived_at": (
                            now - timedelta(days=5) if l_data.get("archived") else None
                        ),
                    },
                )
                if l_created:
                    stats["listings"] += 1
                    photo, ph_created = ListingPhoto.objects.get_or_create(
                        listing=listing,
                        order=0,
                        defaults={"photo_path": l_data["photo"]},
                    )
                    if ph_created:
                        stats["photos"] += 1

        # 4. Pending Verifications
        pending_fixtures = [
            {
                "email": "pending_arif@example.com",
                "display_name": "Arif Hossain",
                "passport_handle": "arif_hossain",
                "phone": "+8801733334444",
                "submitted_delta": timedelta(hours=3),
                "lifestyle": {
                    "gender": LifestyleProfile.Gender.MALE,
                    "occupation": LifestyleProfile.Occupation.STUDENT,
                    "smoking": LifestyleProfile.Smoking.NO,
                    "sleep_schedule": LifestyleProfile.SleepSchedule.FLEXIBLE,
                    "area_preference": ["Mirpur", "Tejgaon"],
                    "budget_min": 3500,
                    "budget_max": 9000,
                },
            },
            {
                "email": "pending_sadia@example.com",
                "display_name": "Sadia Islam",
                "passport_handle": "sadia_islam",
                "phone": "+8801744445555",
                "submitted_delta": timedelta(hours=1),
                "lifestyle": {
                    "gender": LifestyleProfile.Gender.FEMALE,
                    "occupation": LifestyleProfile.Occupation.PRIVATE_JOB,
                    "smoking": LifestyleProfile.Smoking.NO,
                    "sleep_schedule": LifestyleProfile.SleepSchedule.EARLY_BIRD,
                    "area_preference": ["Uttara", "Banani"],
                    "budget_min": 7000,
                    "budget_max": 18000,
                },
            },
        ]

        for p_fix in pending_fixtures:
            user, u_created = User.objects.get_or_create(
                email=p_fix["email"],
                defaults={
                    "display_name": p_fix["display_name"],
                    "email_verified": True,
                    "phone_number": p_fix["phone"],
                },
            )
            if u_created:
                user.set_password(default_pwd)
                user.save()
                stats["users"] += 1

            passport, p_created = Passport.objects.get_or_create(
                user=user,
                defaults={
                    "display_name": p_fix["passport_handle"],
                    "status": Passport.Status.PENDING,
                },
            )
            if p_created:
                stats["passports"] += 1

            Verification.objects.get_or_create(
                passport=passport,
                state=Verification.State.SUBMITTED,
                defaults={
                    "nid_front_path": "sample/nid_front.jpg",
                    "nid_back_path": "sample/nid_back.jpg",
                    "selfie_path": "sample/selfie.jpg",
                    "submitted_at": now - p_fix["submitted_delta"],
                },
            )
            stats["verifications"] += 1

            ls = p_fix["lifestyle"]
            LifestyleProfile.objects.get_or_create(
                passport=passport,
                defaults={
                    "gender": ls["gender"],
                    "occupation": ls["occupation"],
                    "smoking": ls["smoking"],
                    "sleep_schedule": ls["sleep_schedule"],
                    "area_preference": ls["area_preference"],
                    "budget_min": ls["budget_min"],
                    "budget_max": ls["budget_max"],
                },
            )

        # 5. Rejected Verification
        rejected_email = "rejected_kamal@example.com"
        rej_user, created = User.objects.get_or_create(
            email=rejected_email,
            defaults={
                "display_name": "Kamal Uddin",
                "email_verified": True,
                "phone_number": "+8801755556666",
            },
        )
        if created:
            rej_user.set_password(default_pwd)
            rej_user.save()
            stats["users"] += 1

        rej_passport, p_created = Passport.objects.get_or_create(
            user=rej_user,
            defaults={
                "display_name": "kamal_uddin",
                "status": Passport.Status.REJECTED,
            },
        )
        if p_created:
            stats["passports"] += 1

        Verification.objects.get_or_create(
            passport=rej_passport,
            state=Verification.State.REJECTED,
            defaults={
                "nid_front_path": "sample/nid_front.jpg",
                "nid_back_path": "sample/nid_back.jpg",
                "selfie_path": "sample/selfie.jpg",
                "submitted_at": now - timedelta(hours=14),
                "last_rejection_at": now - timedelta(hours=12),
                "reject_reason": RejectReason.ILLEGIBLE,
                "reviewer_notes": (
                    "NID photo was unreadable and blurry. "
                    "Please submit high-resolution scans."
                ),
                "reviewed_by": reviewer_user,
                "reviewed_at": now - timedelta(hours=12),
            },
        )
        stats["verifications"] += 1

        LifestyleProfile.objects.get_or_create(
            passport=rej_passport,
            defaults={
                "gender": LifestyleProfile.Gender.MALE,
                "occupation": LifestyleProfile.Occupation.FREELANCER,
                "smoking": LifestyleProfile.Smoking.YES,
                "sleep_schedule": LifestyleProfile.SleepSchedule.NIGHT_OWL,
                "area_preference": ["Mohammadpur"],
                "budget_min": 4000,
                "budget_max": 10000,
            },
        )

        # 6. Unverified Tenant with Passport
        unverified_email = "unverified_tariq@example.com"
        unver_user, created = User.objects.get_or_create(
            email=unverified_email,
            defaults={
                "display_name": "Tariq Rahman",
                "email_verified": True,
                "phone_number": "+8801766667777",
            },
        )
        if created:
            unver_user.set_password(default_pwd)
            unver_user.save()
            stats["users"] += 1

        unver_passport, p_created = Passport.objects.get_or_create(
            user=unver_user,
            defaults={
                "display_name": "tariq_rahman",
                "status": Passport.Status.UNVERIFIED,
            },
        )
        if p_created:
            stats["passports"] += 1

        LifestyleProfile.objects.get_or_create(
            passport=unver_passport,
            defaults={
                "gender": LifestyleProfile.Gender.MALE,
                "occupation": LifestyleProfile.Occupation.STUDENT,
                "smoking": LifestyleProfile.Smoking.NO,
                "sleep_schedule": LifestyleProfile.SleepSchedule.FLEXIBLE,
                "area_preference": ["Dhanmondi"],
                "budget_min": 5000,
                "budget_max": 12000,
            },
        )

        # 7. Freshly Registered User with OTP
        new_email = "fresh_signup@example.com"
        fresh_user, created = User.objects.get_or_create(
            email=new_email,
            defaults={
                "display_name": "Fresh Signup",
                "email_verified": False,
                "phone_number": "+8801777778888",
            },
        )
        if created:
            fresh_user.set_password(default_pwd)
            fresh_user.save()
            stats["users"] += 1

        raw_otp = "123456"
        token_hash = hashlib.sha256(raw_otp.encode("utf-8")).hexdigest()
        EmailVerificationToken.objects.get_or_create(
            user=fresh_user,
            token_hash=token_hash,
            defaults={
                "expires_at": now + timedelta(minutes=15),
                "resend_count": 0,
            },
        )

        return stats

    def _print_summary(self, stats: dict[str, int], default_pwd: str) -> None:
        """Print a helpful summary of seeded credentials and dataset counts."""
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.HTTP_INFO("📊 SEEDED DATASET SUMMARY"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"  • Users created/present:        {stats['users']}")
        self.stdout.write(f"  • Passports created/present:    {stats['passports']}")
        self.stdout.write(f"  • Verifications populated:      {stats['verifications']}")
        self.stdout.write(f"  • Listings populated:           {stats['listings']}")
        self.stdout.write(f"  • Photos populated:             {stats['photos']}")
        self.stdout.write("-" * 70)
        self.stdout.write(self.style.HTTP_INFO("🔑 TEST ACCOUNTS & CREDENTIALS"))
        self.stdout.write("-" * 70)
        self.stdout.write(
            "  1. Superuser / Admin:\n"
            "     Email:    admin@bashapass.com\n"
            "     Password: admin123456\n"
            "     Access:   Django Admin (/admin/)\n"
        )
        self.stdout.write(
            "  2. Staff Reviewer:\n"
            "     Email:    reviewer@bashapass.com\n"
            "     Password: reviewer123456\n"
            "     Access:   Verification Review Queue\n"
        )
        self.stdout.write(
            f"  3. Verified Tenants (Password: '{default_pwd}'):\n"
            "     - tanvir@example.com      (Dhanmondi, 2 listings)\n"
            "     - nusrat@example.com      (Banani, 2 listings)\n"
            "     - sakib@example.com       (Bashundhara, active/withdrawn/archived)\n"
            "     - rahim@example.com       (Gazipur, 1 listing)\n"
            "     - farhana@example.com     (Ramna/Dhanmondi, 2 listings)\n"
            "     - asif@example.com        (Baridhara, 1 listing)\n"
        )
        self.stdout.write(
            f"  4. Pending Verification Queue (Password: '{default_pwd}'):\n"
            "     - pending_arif@example.com\n"
            "     - pending_sadia@example.com\n"
        )
        self.stdout.write(
            f"  5. Verification Cooldown/Rejected (Password: '{default_pwd}'):\n"
            "     - rejected_kamal@example.com\n"
        )
        self.stdout.write(
            f"  6. Unverified Passport (Password: '{default_pwd}'):\n"
            "     - unverified_tariq@example.com\n"
        )
        self.stdout.write(
            f"  7. Fresh Signup (OTP Code: '123456', Password: '{default_pwd}'):\n"
            "     - fresh_signup@example.com\n"
        )
        self.stdout.write("=" * 70)
