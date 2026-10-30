"""Tests for AuditEntry model and append-only constraints (AD-15)."""

import uuid

import pytest
from django.core.exceptions import ValidationError

from apps.audit.models import AuditEntry


@pytest.mark.django_db
class TestAuditEntryModel:
    """Test suite for append-only AuditEntry model."""

    def test_create_audit_entry_success(self) -> None:
        actor_id = uuid.uuid4()
        target_id = uuid.uuid4()
        entry = AuditEntry.objects.create(
            actor_id=actor_id,
            target_type="verification.Verification",
            target_id=target_id,
            action="submit",
            before_state={},
            after_state={"state": "submitted"},
            reason_code=None,
        )
        assert isinstance(entry.id, uuid.UUID)
        assert entry.actor_id == actor_id
        assert entry.target_type == "verification.Verification"
        assert entry.target_id == target_id
        assert entry.action == "submit"
        assert entry.after_state == {"state": "submitted"}
        assert "submit on verification.Verification by" in str(entry)

    def test_audit_entry_immutable_cannot_be_updated(self) -> None:
        actor_id = uuid.uuid4()
        target_id = uuid.uuid4()
        entry = AuditEntry.objects.create(
            actor_id=actor_id,
            target_type="verification.Verification",
            target_id=target_id,
            action="submit",
        )

        entry.action = "tampered_action"
        with pytest.raises(ValidationError, match="append-only and cannot be updated"):
            entry.save()

    def test_audit_entry_immutable_cannot_be_deleted(self) -> None:
        actor_id = uuid.uuid4()
        target_id = uuid.uuid4()
        entry = AuditEntry.objects.create(
            actor_id=actor_id,
            target_type="verification.Verification",
            target_id=target_id,
            action="submit",
        )

        with pytest.raises(ValidationError, match="immutable and cannot be deleted"):
            entry.delete()
