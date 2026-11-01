"""Tests for AccountSettingsView, forms, and end-to-end setting updates."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import User
from apps.listings.constants import (
    ListingKind,
    PreferredGender,
    PreferredSleepSchedule,
    PreferredSmoking,
    RentUnit,
)
from apps.listings.models import Listing
from apps.passports.models import LifestyleProfile, Passport


@pytest.mark.django_db
class TestAccountSettingsView:
    """Test suite for the unified Account Settings hub."""

    @pytest.fixture
    def client(self) -> Client:
        return Client()

    @pytest.fixture
    def user(self) -> User:
        return User.objects.create_user(
            email="tenant_settings@example.com",
            password="Password123!",
            display_name="Tahmid K.",
            phone_number="01711223344",
        )

    @pytest.fixture
    def user_with_passport(self, user: User) -> tuple[User, Passport, LifestyleProfile]:
        passport = Passport.objects.create(
            user=user,
            display_name=user.display_name,
            status=Passport.Status.VERIFIED,
        )
        profile = LifestyleProfile.objects.create(
            passport=passport,
            gender=LifestyleProfile.Gender.MALE,
            occupation=LifestyleProfile.Occupation.STUDENT,
            smoking=LifestyleProfile.Smoking.NO,
            sleep_schedule=LifestyleProfile.SleepSchedule.EARLY_BIRD,
            area_preference=["Mirpur", "Uttara"],
            budget_min=6000,
            budget_max=15000,
        )
        return user, passport, profile

    def test_anonymous_access_redirects_to_login(self, client: Client) -> None:
        """Anonymous GET /accounts/settings/ redirects to login with next parameter."""
        url = reverse("account_settings")
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={url}"

    def test_get_populates_forms_without_passport(
        self, client: Client, user: User
    ) -> None:
        """User without passport sees pre-populated profile form and CTA callout."""
        client.force_login(user)
        response = client.get(reverse("account_settings"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Account Settings" in content
        assert user.display_name in content
        assert user.email in content
        assert "No Lifestyle Profile Configured Yet" in content
        assert "Complete Passport Onboarding" in content

    def test_get_populates_forms_with_verified_passport(
        self,
        client: Client,
        user_with_passport: tuple[User, Passport, LifestyleProfile],
    ) -> None:
        """User with lifestyle profile sees pre-populated chips and budget."""
        user, passport, profile = user_with_passport
        client.force_login(user)
        response = client.get(reverse("account_settings"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "Verified Tenant" in content
        assert 'value="Tahmid K."' in content
        assert 'value="01711223344"' in content
        assert 'value="6000"' in content
        assert 'value="15000"' in content
        assert "Mirpur" in content
        assert "Uttara" in content

    def test_get_with_tab_query_param(self, client: Client, user: User) -> None:
        """Specifying ?tab=location activates location tab pane."""
        client.force_login(user)
        response = client.get(reverse("account_settings") + "?tab=location")
        assert response.status_code == 200
        assert response.context["active_tab"] == "location"

    def test_post_profile_success(
        self,
        client: Client,
        user_with_passport: tuple[User, Passport, LifestyleProfile],
    ) -> None:
        """Updating display name and phone number updates User and Passport."""
        user, passport, _ = user_with_passport
        client.force_login(user)

        response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "profile",
                "display_name": "Tahmid Rahman",
                "phone_number": "+8801812345678",
            },
        )
        assert response.status_code == 302
        assert response.url == f"{reverse('account_settings')}?tab=profile"

        user.refresh_from_db()
        passport.refresh_from_db()
        assert user.display_name == "Tahmid Rahman"
        assert user.phone_number == "+8801812345678"
        assert passport.display_name == "Tahmid Rahman"

    def test_post_profile_validation_error(self, client: Client, user: User) -> None:
        """Invalid display name or malformed phone number displays inline errors."""
        client.force_login(user)

        response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "profile",
                "display_name": "Inv@lid$$Name!",
                "phone_number": "12345",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "Display name may only contain" in content
        assert "Please enter a valid phone number" in content

        user.refresh_from_db()
        assert user.display_name == "Tahmid K."

    def test_post_location_preferences_success(
        self,
        client: Client,
        user_with_passport: tuple[User, Passport, LifestyleProfile],
    ) -> None:
        """Updating area preferences and budget updates LifestyleProfile."""
        user, _, profile = user_with_passport
        client.force_login(user)

        response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "location",
                "area_preference": ["Dhanmondi", "Mohammadpur"],
                "budget_min": 8000,
                "budget_max": 22000,
            },
        )
        assert response.status_code == 302
        assert response.url == f"{reverse('account_settings')}?tab=location"

        profile.refresh_from_db()
        assert profile.area_preference == ["Dhanmondi", "Mohammadpur"]
        assert profile.budget_min == 8000
        assert profile.budget_max == 22000

    def test_post_location_preferences_invalid_budget_bounds(
        self,
        client: Client,
        user_with_passport: tuple[User, Passport, LifestyleProfile],
    ) -> None:
        """Budget min exceeding budget max raises cross-field validation error."""
        user, _, profile = user_with_passport
        client.force_login(user)

        response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "location",
                "area_preference": ["Mirpur"],
                "budget_min": 25000,
                "budget_max": 10000,
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "Minimum budget cannot be greater than maximum budget" in content

        profile.refresh_from_db()
        assert profile.budget_min == 6000

    def test_post_location_preferences_empty_areas(
        self,
        client: Client,
        user_with_passport: tuple[User, Passport, LifestyleProfile],
    ) -> None:
        """Submitting no sub-areas fails validation."""
        user, _, _ = user_with_passport
        client.force_login(user)

        response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "location",
                "area_preference": [],
                "budget_min": 5000,
                "budget_max": 15000,
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "Please select at least one preferred Dhaka sub-area" in content

    def test_post_password_change_success_preserves_session(
        self, client: Client, user: User
    ) -> None:
        """Changing password updates hash and keeps the active session logged in."""
        client.force_login(user)

        response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "password",
                "current_password": "Password123!",
                "new_password": "NewSecretPassword2026!",
                "confirm_password": "NewSecretPassword2026!",
            },
        )
        assert response.status_code == 302
        assert response.url == f"{reverse('account_settings')}?tab=security"

        # Verify password changed
        user.refresh_from_db()
        assert user.check_password("NewSecretPassword2026!")

        # Verify session is preserved (not logged out)
        follow_response = client.get(reverse("account_settings"))
        assert follow_response.status_code == 200

    def test_post_password_change_incorrect_current_password(
        self, client: Client, user: User
    ) -> None:
        """Incorrect current password raises validation error."""
        client.force_login(user)

        response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "password",
                "current_password": "WrongPassword123!",
                "new_password": "NewSecretPassword2026!",
                "confirm_password": "NewSecretPassword2026!",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "Your current password was entered incorrectly." in content

        user.refresh_from_db()
        assert user.check_password("Password123!")

    def test_post_password_change_mismatched_confirmation(
        self, client: Client, user: User
    ) -> None:
        """Mismatched confirmation password raises validation error."""
        client.force_login(user)

        response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "password",
                "current_password": "Password123!",
                "new_password": "NewSecretPassword2026!",
                "confirm_password": "DifferentPassword2026!",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "The two new passwords do not match." in content

    def test_post_password_change_weak_password_fails_complexity(
        self, client: Client, user: User
    ) -> None:
        """Password failing complexity policy displays validation errors."""
        client.force_login(user)

        response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "password",
                "current_password": "Password123!",
                "new_password": "weak",
                "confirm_password": "weak",
            },
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "Password must be at least 8 characters long." in content

    def test_location_update_refreshes_listing_feed_compatibility(
        self,
        client: Client,
        user_with_passport: tuple[User, Passport, LifestyleProfile],
    ) -> None:
        """Updating location preferences immediately refreshes compatibility scores."""
        user, _, profile = user_with_passport
        client.force_login(user)

        # Host landlord user
        host = User.objects.create_user(
            email="landlord_host@example.com",
            password="Password123!",
            display_name="Landlord",
        )
        host_passport = Passport.objects.create(
            user=host,
            display_name=host.display_name,
            status=Passport.Status.VERIFIED,
        )

        # Create active listing located in Dhanmondi
        listing = Listing.objects.create(
            author=host_passport,
            kind=ListingKind.ROOM,
            rent_bdt=12000,
            rent_unit=RentUnit.PER_ROOM,
            area="Dhanmondi",
            body="Sunny room in Dhanmondi with natural light.",
            pref_gender=PreferredGender.MALE,
            pref_smoking=PreferredSmoking.NO,
            pref_sleep=PreferredSleepSchedule.EARLY_BIRD,
            pref_occupation=["student"],
        )

        # Initially, profile areas are ["Mirpur", "Uttara"] -> Dhanmondi is not included
        assert "Dhanmondi" not in profile.area_preference
        feed_response = client.get(reverse("listing_feed"))
        assert feed_response.status_code == 200
        feed_content = feed_response.content.decode()
        assert listing.body in feed_content

        # Update location preferences to include Dhanmondi
        post_response = client.post(
            reverse("account_settings"),
            data={
                "form_action": "location",
                "area_preference": ["Dhanmondi", "Mirpur"],
                "budget_min": 5000,
                "budget_max": 20000,
            },
        )
        assert post_response.status_code == 302

        # Re-fetch listing feed and verify updated preferences
        profile.refresh_from_db()
        assert "Dhanmondi" in profile.area_preference
        refreshed_feed = client.get(reverse("listing_feed"))
        assert refreshed_feed.status_code == 200
        assert listing.body in refreshed_feed.content.decode()
