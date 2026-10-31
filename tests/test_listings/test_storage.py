"""Tests for ListingPhotoStorageService (Story 019)."""

import uuid

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.listings.services.storage import ListingPhotoStorageService

VALID_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\xff\xc0\x00\x0b\x08\x00\x10\x00\x10\x01\x01\x11\x00"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)


@pytest.fixture
def valid_image_file() -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name="test_listing.jpg",
        content=VALID_JPEG_BYTES,
        content_type="image/jpeg",
    )


@pytest.fixture
def fake_corrupt_file() -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name="fake_image.jpg",
        content=b"THIS_IS_NOT_A_VALID_IMAGE_HEADER_MALICIOUS_BYTES",
        content_type="image/jpeg",
    )


class TestListingPhotoStorageService:
    """Test suite for photo validation and persistence operations."""

    def test_validate_photo_success(self, valid_image_file: SimpleUploadedFile) -> None:
        ListingPhotoStorageService.validate_photo_file(valid_image_file)

    def test_validate_photo_rejects_corrupted_payload(
        self, fake_corrupt_file: SimpleUploadedFile
    ) -> None:
        with pytest.raises(ValidationError) as exc:
            ListingPhotoStorageService.validate_photo_file(fake_corrupt_file)
        assert "not a valid JPEG, PNG, or WebP image" in str(exc.value)

    def test_validate_photo_rejects_large_file(self) -> None:
        large_content = b"0" * (6 * 1024 * 1024)  # 6 MB
        large_file = SimpleUploadedFile(
            name="too_big.jpg", content=large_content, content_type="image/jpeg"
        )
        with pytest.raises(ValidationError) as exc:
            ListingPhotoStorageService.validate_photo_file(large_file)
        assert "exceeds maximum permitted size" in str(exc.value)

    def test_validate_photo_rejects_disallowed_extension(self) -> None:
        invalid_ext_file = SimpleUploadedFile(
            name="script.exe", content=b"fake", content_type="image/jpeg"
        )
        with pytest.raises(ValidationError) as exc:
            ListingPhotoStorageService.validate_photo_file(invalid_ext_file)
        assert "Unsupported image format" in str(exc.value)

    def test_validate_batch_cardinality(
        self, valid_image_file: SimpleUploadedFile
    ) -> None:
        # Zero photos
        with pytest.raises(ValidationError) as exc_zero:
            ListingPhotoStorageService.validate_photo_batch([])
        assert "At least 1 photo is required" in str(exc_zero.value)

        # > 7 photos
        files_8 = [valid_image_file] * 8
        with pytest.raises(ValidationError) as exc_max:
            ListingPhotoStorageService.validate_photo_batch(files_8)
        assert "at most 7 photos" in str(exc_max.value)

    def test_save_and_delete_photo(self, valid_image_file: SimpleUploadedFile) -> None:
        listing_id = uuid.uuid4()
        rel_path = ListingPhotoStorageService.save_photo(
            file=valid_image_file,
            listing_id=listing_id,
            order=0,
        )
        assert f"listings/photos/{listing_id}/photo_0_" in rel_path
        abs_path = ListingPhotoStorageService.get_absolute_path(rel_path)
        assert abs_path is not None
        assert abs_path.is_file()

        # Delete photo
        deleted = ListingPhotoStorageService.delete_photo(rel_path)
        assert deleted is True
        assert not abs_path.is_file()
