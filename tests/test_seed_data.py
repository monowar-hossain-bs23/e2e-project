"""Tests for seed_data and seed management commands."""

import io

import pytest
from django.core.management import call_command

from apps.accounts.models import EmailVerificationToken, User
from apps.listings.models import Listing, ListingPhoto
from apps.passports.models import Passport
from apps.verification.models import Verification


@pytest.mark.django_db
class TestSeedDataCommand:
    """Test suite verifying seed_data and seed commands."""

    def test_seed_data_populates_expected_entities(self) -> None:
        """Verify seed_data creates accounts, passports, and listings."""
        out = io.StringIO()
        call_command("seed_data", stdout=out)
        output = out.getvalue()

        assert "Database seeding successfully completed" in output

        # Check Admin
        admin = User.objects.filter(email="admin@bashapass.com").first()
        assert admin is not None
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.check_password("admin123456")

        # Check Reviewer
        reviewer = User.objects.filter(email="reviewer@bashapass.com").first()
        assert reviewer is not None
        assert reviewer.is_staff is True
        assert reviewer.is_superuser is False
        assert reviewer.check_password("reviewer123456")

        # Check Verified User & Passport
        tanvir = User.objects.filter(email="tanvir@example.com").first()
        assert tanvir is not None
        assert tanvir.passport.status == Passport.Status.VERIFIED
        assert hasattr(tanvir.passport, "lifestyle_profile")
        assert tanvir.passport.listings.count() >= 2

        # Check Listings
        assert Listing.objects.filter(area="Dhanmondi").exists()
        assert Listing.objects.filter(area="Banani").exists()
        assert Listing.objects.filter(archived_at__isnull=False).exists()
        assert Listing.objects.filter(withdrawn_at__isnull=False).exists()
        assert ListingPhoto.objects.count() >= 5

        # Check Pending verifications in queue
        pending_verifications = Verification.objects.filter(
            state=Verification.State.SUBMITTED
        )
        assert pending_verifications.count() >= 2

        # Check Rejected verification
        rejected_ver = Verification.objects.filter(
            state=Verification.State.REJECTED
        ).first()
        assert rejected_ver is not None
        assert rejected_ver.reject_reason == "illegible"
        assert rejected_ver.last_rejection_at is not None

        # Check Fresh Signup with OTP token
        fresh_user = User.objects.filter(email="fresh_signup@example.com").first()
        assert fresh_user is not None
        assert fresh_user.email_verified is False
        assert EmailVerificationToken.objects.filter(user=fresh_user).exists()

    def test_seed_data_is_idempotent(self) -> None:
        """Calling seed_data repeatedly should not duplicate or error."""
        out1 = io.StringIO()
        call_command("seed_data", stdout=out1)

        out2 = io.StringIO()
        call_command("seed_data", stdout=out2)

        admin_count = User.objects.filter(email="admin@bashapass.com").count()
        assert admin_count == 1

    def test_seed_data_clear_flag(self) -> None:
        """Calling seed_data with --clear wipes prior entities and seeds afresh."""
        call_command("seed_data")
        initial_users_count = User.objects.count()
        assert initial_users_count > 0

        out = io.StringIO()
        call_command("seed_data", "--clear", stdout=out)
        assert "Existing data cleared" in out.getvalue()
        assert User.objects.count() == initial_users_count

    def test_seed_alias_command(self) -> None:
        """Verify the 'seed' alias command also functions properly."""
        out = io.StringIO()
        call_command("seed", stdout=out)
        assert "Database seeding successfully completed" in out.getvalue()
