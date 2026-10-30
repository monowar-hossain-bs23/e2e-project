"""URL configuration for verification media and staff inspection endpoints."""

from django.urls import path

from apps.verification.views import private_document_stream_view

urlpatterns = [
    path(
        "admin/verification/media/<uuid:verification_id>/<str:doc_type>/",
        private_document_stream_view,
        name="admin_verification_media",
    ),
]
