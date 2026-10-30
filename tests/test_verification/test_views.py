"""Tests for staff-only private document streaming view (AD-9, ADR-002)."""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.passports.models import Passport
from apps.verification.models import Verification
from apps.verification.services.storage import VerificationStorageService

User = get_user_model()


@pytest.mark.django_db
class TestPrivateDocumentStreamView:
    """Test access control and streaming for private document inspection."""

    @pytest.fixture
    def client(self) -> Client:
        return Client()

    @pytest.fixture
    def staff_user(self) -> User:
        return User.objects.create_user(
            email="staff_stream@example.com",
            password="Password123!",
            display_name="Staff Streamer",
            is_staff=True,
        )

    @pytest.fixture
    def regular_user(self) -> User:
        return User.objects.create_user(
            email="regular_stream@example.com",
            password="Password123!",
            display_name="Regular User",
            is_staff=False,
        )

    @pytest.fixture
    def verification_with_files(self) -> Verification:
        tenant = User.objects.create_user(
            email="tenant_stream@example.com",
            password="Password123!",
            display_name="Tenant Streamer",
        )
        passport = Passport.objects.create(
            user=tenant,
            display_name="StreamTenant",
        )

        test_file = SimpleUploadedFile(
            "sample_nid.jpg",
            b"\xff\xd8\xfffake-jpeg-data",
            content_type="image/jpeg",
        )
        saved_rel_path = VerificationStorageService.save_file(
            file=test_file,
            passport_id=passport.pk,
            doc_type="nid_front",
        )

        return Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path=saved_rel_path,
            nid_back_path="",
            selfie_path="",
            submitted_at=timezone.now(),
        )

    def test_anonymous_access_redirected(
        self, client: Client, verification_with_files: Verification
    ) -> None:
        url = reverse(
            "admin_verification_media",
            kwargs={
                "verification_id": verification_with_files.pk,
                "doc_type": "nid_front",
            },
        )
        response = client.get(url)
        # staff_member_required redirects unauthenticated users to login
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_regular_user_access_redirected(
        self,
        client: Client,
        regular_user: User,
        verification_with_files: Verification,
    ) -> None:
        client.force_login(regular_user)
        url = reverse(
            "admin_verification_media",
            kwargs={
                "verification_id": verification_with_files.pk,
                "doc_type": "nid_front",
            },
        )
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_invalid_doc_type_returns_404(
        self,
        client: Client,
        staff_user: User,
        verification_with_files: Verification,
    ) -> None:
        client.force_login(staff_user)
        url = reverse(
            "admin_verification_media",
            kwargs={
                "verification_id": verification_with_files.pk,
                "doc_type": "unsupported_doc",
            },
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_nonexistent_verification_id_returns_404(
        self, client: Client, staff_user: User
    ) -> None:
        client.force_login(staff_user)
        url = reverse(
            "admin_verification_media",
            kwargs={
                "verification_id": uuid.uuid4(),
                "doc_type": "nid_front",
            },
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_missing_file_on_disk_returns_404(
        self,
        client: Client,
        staff_user: User,
        verification_with_files: Verification,
    ) -> None:
        client.force_login(staff_user)
        # nid_back_path is empty on the fixture
        url = reverse(
            "admin_verification_media",
            kwargs={
                "verification_id": verification_with_files.pk,
                "doc_type": "nid_back",
            },
        )
        response = client.get(url)
        assert response.status_code == 404

    def test_staff_access_valid_file_returns_streaming_response(
        self,
        client: Client,
        staff_user: User,
        verification_with_files: Verification,
    ) -> None:
        client.force_login(staff_user)
        url = reverse(
            "admin_verification_media",
            kwargs={
                "verification_id": verification_with_files.pk,
                "doc_type": "nid_front",
            },
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "image/" in response.headers.get("Content-Type", "")
        assert "inline;" in response.headers.get("Content-Disposition", "")

        # Verify streamed bytes
        content = b"".join(response.streaming_content)
        assert content == b"\xff\xd8\xfffake-jpeg-data"
