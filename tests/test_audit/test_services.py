"""Tests for AuditService orchestration (AD-15)."""

import uuid

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEntry
from apps.audit.services.audit_service import AuditService
from apps.passports.models import Passport

User = get_user_model()


@pytest.mark.django_db
class TestAuditService:
    """Test suite for AuditService.append operation."""

    @pytest.fixture
    def sample_passport(self) -> Passport:
        user = User.objects.create_user(
            email="audit_user@example.com",
            password="Password123!",
            display_name="Audit User",
        )
        return Passport.objects.create(
            user=user,
            display_name="AuditUser",
        )

    def test_append_creates_entry_with_uuid_actor(
        self, sample_passport: Passport
    ) -> None:
        actor_id = uuid.uuid4()
        entry = AuditService.append(
            actor_id=actor_id,
            target=sample_passport,
            action="create",
            before_state={},
            after_state={"status": "unverified"},
            reason_code="none",
        )
        assert isinstance(entry, AuditEntry)
        assert entry.actor_id == actor_id
        assert entry.target_type == "passports.passport"
        assert entry.target_id == sample_passport.pk
        assert entry.action == "create"
        assert entry.after_state == {"status": "unverified"}
        assert entry.reason_code == "none"

    def test_append_creates_entry_with_string_actor(
        self, sample_passport: Passport
    ) -> None:
        actor_id = uuid.uuid4()
        entry = AuditService.append(
            actor_id=str(actor_id),
            target=sample_passport,
            action="update",
        )
        assert entry.actor_id == actor_id
        assert entry.before_state == {}
        assert entry.after_state == {}
        assert entry.reason_code is None
