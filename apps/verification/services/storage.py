"""Private PII file storage service isolating documents under media_private/ (AD-9)."""

import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES: set[str] = {
    "image/jpeg",
    "image/pjpeg",
    "image/png",
    "image/webp",
}


class VerificationStorageService:
    """Service managing private PII documents outside the public media tree."""

    @classmethod
    def get_private_root(cls) -> Path:
        """Return Path to private media directory, creating if needed."""
        default_dir = settings.BASE_DIR / "media_private"
        root = Path(getattr(settings, "MEDIA_PRIVATE_ROOT", default_dir))
        root.mkdir(parents=True, exist_ok=True)
        return root

    @classmethod
    def validate_file(cls, file: UploadedFile) -> None:
        """Validate uploaded document file size and type."""
        if not file:
            raise ValidationError(_("A document file is required."))

        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        if file.size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                _(f"File size exceeds maximum permitted limit of {max_mb} MB.")
            )

        name = file.name or ""
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise ValidationError(
                _(f"Unsupported file format '{ext}'. Allowed formats: {allowed}.")
            )

        content_type = getattr(file, "content_type", "")
        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                _(
                    f"Unsupported content type '{content_type}'. "
                    "Must be a JPEG, PNG, or WebP image."
                )
            )

    @classmethod
    def save_file(
        cls,
        *,
        file: UploadedFile,
        passport_id: uuid.UUID | str,
        doc_type: str,
    ) -> str:
        """Save an uploaded file to private storage and return its relative path.

        Args:
            file: The uploaded file object.
            passport_id: Passport UUID for folder partitioning.
            doc_type: Document descriptor ('nid_front', 'nid_back', 'selfie').

        Returns:
            Relative path string inside MEDIA_PRIVATE_ROOT.
        """
        cls.validate_file(file)

        ext = os.path.splitext(file.name or "")[1].lower() or ".jpg"
        unique_token = uuid.uuid4().hex[:12]
        filename = f"{doc_type}_{unique_token}{ext}"

        rel_dir = Path("verifications") / str(passport_id)
        target_dir = cls.get_private_root() / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / filename

        with open(target_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Return posix relative path string
        return (rel_dir / filename).as_posix()

    @classmethod
    def get_absolute_path(cls, relative_path: str) -> Path | None:
        """Resolve a relative path inside MEDIA_PRIVATE_ROOT securely,

        preventing directory traversal attacks.
        """
        if not relative_path:
            return None

        private_root = cls.get_private_root().resolve()
        candidate = (private_root / relative_path).resolve()

        # Path traversal guard: candidate must be strictly within private_root
        if not candidate.is_relative_to(private_root):
            return None

        if not candidate.is_file():
            return None

        return candidate
