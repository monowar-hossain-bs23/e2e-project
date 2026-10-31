"""VerificationService: Sole mutator of verification states and cooldowns."""

import logging
from datetime import timedelta
from typing import Any

from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.audit.services.audit_service import AuditService
from apps.passports.models import Passport
from apps.verification.models import Verification
from apps.verification.services.reject_reasons import RejectReason
from apps.verification.services.storage import VerificationStorageService

logger = logging.getLogger(__name__)

COOLDOWN_HOURS: int = 24


class VerificationService:
    """Sole mutator governing verification lifecycle, cooldowns, and audit logging."""

    @classmethod
    def check_cooldown(cls, passport: Passport) -> dict[str, Any]:
        """Check if passport is restricted by the 24-hour cooldown (FR-9)."""
        latest_rejection = (
            Verification.objects.filter(
                passport=passport,
                state=Verification.State.REJECTED,
                last_rejection_at__isnull=False,
            )
            .order_by("-last_rejection_at")
            .first()
        )

        if latest_rejection and latest_rejection.last_rejection_at:
            cooldown_period = timedelta(hours=COOLDOWN_HOURS)
            elapsed = timezone.now() - latest_rejection.last_rejection_at
            if elapsed < cooldown_period:
                remaining_seconds = int((cooldown_period - elapsed).total_seconds())
                cooldown_until = latest_rejection.last_rejection_at + cooldown_period
                return {
                    "cooldown_active": True,
                    "remaining_seconds": max(0, remaining_seconds),
                    "cooldown_until": cooldown_until,
                    "last_rejection_at": latest_rejection.last_rejection_at,
                    "reject_reason": latest_rejection.reject_reason,
                }

        return {
            "cooldown_active": False,
            "remaining_seconds": 0,
            "cooldown_until": None,
            "last_rejection_at": None,
            "reject_reason": None,
        }

    @classmethod
    def submit_verification(
        cls,
        *,
        passport: Passport,
        actor: Any,
        nid_front_file: Any,
        nid_back_file: Any,
        selfie_file: Any,
    ) -> dict[str, Any]:
        """Submit identity documents for verification review."""
        if not (actor.is_staff or actor.pk == passport.user.pk):
            return {
                "ok": False,
                "code": "forbidden_role",
                "message": _("You are not authorized to submit for this passport."),
            }

        cooldown = cls.check_cooldown(passport)
        if cooldown["cooldown_active"]:
            hrs = max(1, cooldown["remaining_seconds"] // 3600)
            return {
                "ok": False,
                "code": "cooldown_active",
                "message": _(
                    f"A 24-hour waiting period is in place following your previous "
                    f"rejection. Please wait approximately {hrs} hour(s) before "
                    f"submitting new verification documents."
                ),
                "remaining_seconds": cooldown["remaining_seconds"],
                "cooldown_until": cooldown["cooldown_until"],
            }

        try:
            front_path = VerificationStorageService.save_file(
                file=nid_front_file,
                passport_id=passport.pk,
                doc_type="nid_front",
            )
            back_path = VerificationStorageService.save_file(
                file=nid_back_file,
                passport_id=passport.pk,
                doc_type="nid_back",
            )
            selfie_path = VerificationStorageService.save_file(
                file=selfie_file,
                passport_id=passport.pk,
                doc_type="selfie",
            )
        except Exception as exc:
            logger.warning(
                "File validation failed for passport %s: %s", passport.pk, exc
            )
            return {
                "ok": False,
                "code": "invalid_files",
                "message": str(exc),
            }

        with transaction.atomic():
            now = timezone.now()
            verification = Verification.objects.create(
                passport=passport,
                state=Verification.State.SUBMITTED,
                nid_front_path=front_path,
                nid_back_path=back_path,
                selfie_path=selfie_path,
                submitted_at=now,
            )

            passport.status = Passport.Status.PENDING
            passport.save(update_fields=["status", "updated_at"])

            AuditService.append(
                actor_id=actor.pk,
                target=verification,
                action="submit",
                after_state={
                    "state": Verification.State.SUBMITTED,
                    "submitted_at": now.isoformat(),
                },
            )

        logger.info(
            "Verification attempt %s submitted for passport %s by actor %s",
            verification.pk,
            passport.pk,
            actor.pk,
        )
        return {"ok": True, "verification": verification}

    @classmethod
    def transition(
        cls,
        *,
        verification: Verification,
        new_state: str,
        actor: Any,
        reason: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Sole mutator for verification state transitions (Architecture Spine AD-2)."""
        if not getattr(actor, "is_staff", False):
            return {
                "ok": False,
                "code": "forbidden_role",
                "message": _(
                    "Only staff members can evaluate verification submissions."
                ),
            }

        valid_states = set(Verification.State.values)
        if new_state not in valid_states:
            return {
                "ok": False,
                "code": "invalid_state",
                "message": _(f"Invalid verification state '{new_state}'."),
            }

        current_state = verification.state

        # Legal state transitions DAG
        legal_next = {
            Verification.State.SUBMITTED: {
                Verification.State.REVIEWING,
                Verification.State.VERIFIED,
                Verification.State.REJECTED,
            },
            Verification.State.REVIEWING: {
                Verification.State.VERIFIED,
                Verification.State.REJECTED,
            },
            Verification.State.VERIFIED: set(),
            Verification.State.REJECTED: set(),
        }

        if new_state not in legal_next.get(current_state, set()):
            return {
                "ok": False,
                "code": "invalid_transition",
                "message": _(
                    f"Illegal state transition from '{current_state}' to '{new_state}'."
                ),
            }

        # Reason code validation for rejections
        canonical_reason = None
        if new_state == Verification.State.REJECTED:
            if not reason:
                return {
                    "ok": False,
                    "code": "missing_reason_code",
                    "message": _(
                        "A canonical reason code is required when "
                        "rejecting a submission."
                    ),
                }
            if reason not in RejectReason.values:
                return {
                    "ok": False,
                    "code": "invalid_reason_code",
                    "message": _(f"Invalid rejection reason code '{reason}'."),
                }
            canonical_reason = reason

        now = timezone.now()
        passport = verification.passport
        rev_by = (
            str(verification.reviewed_by_id) if verification.reviewed_by_id else None
        )
        before_state = {
            "state": verification.state,
            "passport_status": passport.status,
            "reviewed_by": rev_by,
        }

        with transaction.atomic():
            verification.state = new_state
            verification.reviewed_by = actor

            if new_state == Verification.State.VERIFIED:
                verification.reviewed_at = now
                passport.status = Passport.Status.VERIFIED
                passport.save(update_fields=["status", "updated_at"])

            elif new_state == Verification.State.REJECTED:
                verification.reviewed_at = now
                verification.last_rejection_at = now
                verification.reject_reason = canonical_reason
                verification.reviewer_notes = (notes or "").strip()
                passport.status = Passport.Status.REJECTED
                passport.save(update_fields=["status", "updated_at"])

            verification.save()

            after_state = {
                "state": verification.state,
                "passport_status": passport.status,
                "reviewed_by": str(actor.pk),
                "reviewed_at": now.isoformat() if verification.reviewed_at else None,
                "reject_reason": verification.reject_reason,
            }

            AuditService.append(
                actor_id=actor.pk,
                target=verification,
                action="transition",
                before_state=before_state,
                after_state=after_state,
                reason_code=canonical_reason,
            )

        # Direct email notification dispatch within 5 minutes (FR-18)
        if new_state in (Verification.State.VERIFIED, Verification.State.REJECTED):
            cls.send_verification_email(
                verification=verification,
                decision=new_state,
                reason=canonical_reason,
                notes=verification.reviewer_notes,
            )

        logger.info(
            "Verification %s transitioned to %s by staff %s",
            verification.pk,
            new_state,
            actor.pk,
        )
        return {"ok": True, "verification": verification}

    @classmethod
    def send_verification_email(
        cls,
        *,
        verification: Verification,
        decision: str,
        reason: str | None = None,
        notes: str | None = None,
    ) -> bool:
        """Deliver transactional email notification of review decision."""
        passport = verification.passport
        user = passport.user
        display_name = passport.display_name

        context = {
            "display_name": display_name,
            "recipient_email": user.email,
            "dashboard_url": "/dashboard/",
        }

        if decision == Verification.State.VERIFIED:
            subject = "Your Basha Pass Verification is Approved!"
            txt_template = "verification/email/verification_approved.txt"
            html_template = "verification/email/verification_approved.html"
        else:
            reason_map = dict(RejectReason.choices)
            reason_label = reason_map.get(reason or "", reason or "Other")
            cooldown_until = (
                verification.last_rejection_at + timedelta(hours=COOLDOWN_HOURS)
                if verification.last_rejection_at
                else timezone.now() + timedelta(hours=COOLDOWN_HOURS)
            )
            context.update(
                {
                    "reason_label": reason_label,
                    "reviewer_notes": notes,
                    "cooldown_until": cooldown_until,
                }
            )
            subject = "Basha Pass Verification Update"
            txt_template = "verification/email/verification_rejected.txt"
            html_template = "verification/email/verification_rejected.html"

        try:
            body_txt = render_to_string(txt_template, context)
            body_html = render_to_string(html_template, context)

            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=body_txt,
                to=[user.email],
            )
            email_msg.attach_alternative(body_html, "text/html")
            email_msg.send(fail_silently=True)
            return True
        except Exception as exc:
            logger.error("Failed to send verification email to %s: %s", user.email, exc)
            return False
