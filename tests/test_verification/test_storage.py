"""Tests for VerificationStorageService private PII storage (AD-9, ADR-002)."""

import uuid

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.verification.services.storage import (
    MAX_FILE_SIZE_BYTES,
    VerificationStorageService,
)


@pytest.mark.django_db
class TestVerificationStorageService:
    """Test suite for private storage, size/type validation, and traversal defense."""

    def test_validate_file_missing_raises_error(self) -> None:
        with pytest.raises(ValidationError, match="A document file is required"):
            VerificationStorageService.validate_file(None)  # type: ignore[arg-type]

    def test_validate_file_size_exceeded_raises_error(self) -> None:
        oversized_content = b"x" * (MAX_FILE_SIZE_BYTES + 1024)
        large_file = SimpleUploadedFile(
            "nid_front.jpg",
            oversized_content,
            content_type="image/jpeg",
        )
        with pytest.raises(ValidationError, match="File size exceeds maximum"):
            VerificationStorageService.validate_file(large_file)

    def test_validate_file_disallowed_extension_raises_error(self) -> None:
        exe_file = SimpleUploadedFile(
            "malware.exe",
            b"test content",
            content_type="application/x-msdownload",
        )
        with pytest.raises(ValidationError, match="Unsupported file format"):
            VerificationStorageService.validate_file(exe_file)

    def test_validate_file_disallowed_mime_type_raises_error(self) -> None:
        pdf_file = SimpleUploadedFile(
            "document.jpg",
            b"test content",
            content_type="application/pdf",
        )
        with pytest.raises(ValidationError, match="Unsupported content type"):
            VerificationStorageService.validate_file(pdf_file)

    def test_validate_file_valid_images_pass(self) -> None:
        for ext, mime in [
            ("photo.jpg", "image/jpeg"),
            ("photo.jpeg", "image/jpeg"),
            ("photo.png", "image/png"),
            ("photo.webp", "image/webp"),
        ]:
            valid_file = SimpleUploadedFile(ext, b"valid image data", content_type=mime)
            VerificationStorageService.validate_file(valid_file)

    def test_save_file_persists_to_media_private(self) -> None:
        passport_id = uuid.uuid4()
        test_file = SimpleUploadedFile(
            "front.png",
            b"\x89PNG\r\n\x1a\nfake-png-content",
            content_type="image/png",
        )

        rel_path = VerificationStorageService.save_file(
            file=test_file,
            passport_id=passport_id,
            doc_type="nid_front",
        )

        assert rel_path.startswith(f"verifications/{passport_id}/nid_front_")
        assert rel_path.endswith(".png")

        # Confirm file exists on disk inside MEDIA_PRIVATE_ROOT
        abs_path = VerificationStorageService.get_absolute_path(rel_path)
        assert abs_path is not None
        assert abs_path.exists()
        assert abs_path.read_bytes() == b"\x89PNG\r\n\x1a\nfake-png-content"

    def test_get_absolute_path_prevents_directory_traversal(self) -> None:
        # None for empty or None
        assert VerificationStorageService.get_absolute_path("") is None

        # None for non-existent file
        assert (
            VerificationStorageService.get_absolute_path(
                "verifications/nonexistent.jpg"
            )
            is None
        )

        # Directory traversal attempt
        traversal_attempts = [
            "../../../etc/passwd",
            "../config/settings/base.py",
            "/etc/shadow",
            "verifications/../../manage.py",
        ]
        for path in traversal_attempts:
            assert VerificationStorageService.get_absolute_path(path) is None
