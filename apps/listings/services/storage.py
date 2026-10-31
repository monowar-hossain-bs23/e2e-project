"""Public media storage service for accommodation listing photos (ADR-003)."""

import os
import uuid
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.utils.translation import gettext_lazy as _

from apps.listings.constants import (
    MAX_LISTING_PHOTOS,
    MAX_PHOTO_SIZE_BYTES,
    MIN_LISTING_PHOTOS,
)

ALLOWED_PHOTO_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_PHOTO_MIME_TYPES: set[str] = {
    "image/jpeg",
    "image/pjpeg",
    "image/png",
    "image/webp",
}


def validate_image_magic_bytes(file: Any) -> None:
    """Validate that file header contains canonical JPEG, PNG, or WebP magic bytes."""
    file.seek(0)
    header = file.read(12)
    file.seek(0)

    if len(header) < 4:
        raise ValidationError(_("Uploaded file is empty or corrupted."))

    is_jpeg = header.startswith(b"\xff\xd8\xff")
    is_png = header.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = (
        len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    )

    if not (is_jpeg or is_png or is_webp):
        raise ValidationError(
            _("Uploaded file is corrupted or not a valid JPEG, PNG, or WebP image.")
        )


class ListingPhotoStorageService:
    """Service managing public listing photos under media/listings/photos/."""

    @classmethod
    def get_public_root(cls) -> Path:
        """Return Path to public media directory, ensuring existence."""
        default_dir = settings.BASE_DIR / "media"
        root = Path(getattr(settings, "MEDIA_ROOT", default_dir))
        root.mkdir(parents=True, exist_ok=True)
        return root

    @classmethod
    def validate_photo_file(cls, file: Any) -> None:
        """Validate single photo file size, extension, MIME, and Pillow integrity."""
        if not file:
            raise ValidationError(_("A photo file is required."))

        max_mb = MAX_PHOTO_SIZE_BYTES // (1024 * 1024)
        if getattr(file, "size", 0) > MAX_PHOTO_SIZE_BYTES:
            raise ValidationError(
                _(f"Photo exceeds maximum permitted size of {max_mb} MB.")
            )

        name = getattr(file, "name", "") or ""
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_PHOTO_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_PHOTO_EXTENSIONS))
            raise ValidationError(
                _(f"Unsupported image format '{ext}'. Allowed: {allowed}.")
            )

        content_type = getattr(file, "content_type", "")
        if content_type and content_type.lower() not in ALLOWED_PHOTO_MIME_TYPES:
            raise ValidationError(
                _(
                    f"Unsupported content type '{content_type}'. "
                    "Must be JPEG, PNG, or WebP."
                )
            )

        # Inspect image binary magic bytes
        validate_image_magic_bytes(file)

    @classmethod
    def validate_photo_batch(cls, files: list[Any]) -> None:
        """Validate an entire batch of uploaded photos."""
        if not files or len(files) < MIN_LISTING_PHOTOS:
            raise ValidationError(
                _(f"At least {MIN_LISTING_PHOTOS} photo is required for each listing.")
            )
        if len(files) > MAX_LISTING_PHOTOS:
            raise ValidationError(
                _(f"You can upload at most {MAX_LISTING_PHOTOS} photos per listing.")
            )
        for file in files:
            cls.validate_photo_file(file)

    @classmethod
    def save_photo(
        cls,
        *,
        file: Any,
        listing_id: uuid.UUID | str,
        order: int = 0,
    ) -> str:
        """Save a photo file to public media and return its relative path."""
        cls.validate_photo_file(file)

        ext = os.path.splitext(getattr(file, "name", "") or ".jpg")[1].lower()
        if not ext:
            ext = ".jpg"

        file_id = uuid.uuid4().hex[:12]
        rel_dir = f"listings/photos/{str(listing_id)}"
        filename = f"photo_{order}_{file_id}{ext}"
        rel_path = f"{rel_dir}/{filename}"

        root = cls.get_public_root()
        target_dir = root / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        storage = FileSystemStorage(location=str(root))
        storage.save(rel_path, file)

        return rel_path

    @classmethod
    def get_absolute_path(cls, relative_path: str) -> Path | None:
        """Resolve a relative storage path to its absolute filesystem path."""
        if not relative_path:
            return None
        root = cls.get_public_root()
        abs_path = (root / relative_path).resolve()
        if not str(abs_path).startswith(str(root.resolve())):
            return None
        return abs_path

    @classmethod
    def delete_photo(cls, relative_path: str) -> bool:
        """Delete physical file from disk if it exists."""
        abs_path = cls.get_absolute_path(relative_path)
        if abs_path and abs_path.is_file():
            try:
                abs_path.unlink()
                return True
            except OSError:
                return False
        return False
