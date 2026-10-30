"""Staff views for private PII media streaming (AD-9, ADR-002)."""

import mimetypes

from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from apps.verification.models import Verification
from apps.verification.services.storage import VerificationStorageService

VALID_DOC_TYPES = {"nid_front", "nid_back", "selfie"}


@staff_member_required
def private_document_stream_view(
    request: HttpRequest,
    verification_id: str,
    doc_type: str,
) -> HttpResponse:
    """Stream private verification documents to staff members only."""
    if doc_type not in VALID_DOC_TYPES:
        raise Http404("Invalid document type requested.")

    verification = get_object_or_404(Verification, id=verification_id)
    rel_path = getattr(verification, f"{doc_type}_path", None)
    if not rel_path:
        raise Http404("Document path not found on verification record.")

    abs_path = VerificationStorageService.get_absolute_path(rel_path)
    if not abs_path or not abs_path.is_file():
        raise Http404("Private document file does not exist on disk.")

    mime_type, _ = mimetypes.guess_type(str(abs_path))
    content_type = mime_type or "image/jpeg"

    # Streaming file response with staff protection
    response = FileResponse(open(abs_path, "rb"), content_type=content_type)
    response["Content-Disposition"] = f'inline; filename="{abs_path.name}"'
    return response
