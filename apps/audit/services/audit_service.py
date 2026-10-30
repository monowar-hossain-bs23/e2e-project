"""AuditService for appending immutable audit records (AD-15)."""

import logging
import uuid
from typing import Any

from django.db import models

from apps.audit.models import AuditEntry

logger = logging.getLogger(__name__)


class AuditService:
    """Service orchestrating write-once audit log entries."""

    @staticmethod
    def append(
        *,
        actor_id: uuid.UUID | str,
        target: models.Model,
        action: str,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        reason_code: str | None = None,
    ) -> AuditEntry:
        """Create and persist an append-only audit entry.

        Args:
            actor_id: Primary key UUID of the actor performing the action.
            target: The model instance targeted by the action.
            action: Descriptive action string (e.g. 'transition', 'submit').
            before_state: State dictionary before the mutation.
            after_state: State dictionary after the mutation.
            reason_code: Optional canonical reason code (e.g. for rejections).

        Returns:
            The newly created AuditEntry.
        """
        target_app = target._meta.app_label
        target_name = target._meta.model_name
        target_type = f"{target_app}.{target_name}"
        target_id = (
            target.pk if isinstance(target.pk, uuid.UUID) else uuid.UUID(str(target.pk))
        )
        parsed_actor_id = (
            actor_id if isinstance(actor_id, uuid.UUID) else uuid.UUID(str(actor_id))
        )

        entry = AuditEntry.objects.create(
            actor_id=parsed_actor_id,
            target_type=target_type,
            target_id=target_id,
            action=action,
            before_state=before_state or {},
            after_state=after_state or {},
            reason_code=reason_code,
        )

        logger.info(
            "AuditEntry created: action=%s target=%s target_id=%s actor=%s",
            action,
            target_type,
            target_id,
            parsed_actor_id,
        )
        return entry
