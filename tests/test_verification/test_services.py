"""Tests for VerificationService state machine, cooldowns, and notifications."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.audit.models import AuditEntry
from apps.passports.models import Passport
from apps.verification.models import Verification
from apps.verification.services.reject_reasons import RejectReason
from apps.verification.services.verification_service import VerificationService

User = get_user_model()


@pytest.mark.django_db
class TestVerificationService:
    """Test suite for VerificationService mutator operations."""

    @pytest.fixture
    def tenant_user(self) -> User:
        return User.objects.create_user(
            email="tenant@example.com",
            password="Password123!",
            display_name="Tenant User",
        )

    @pytest.fixture
    def staff_user(self) -> User:
        return User.objects.create_user(
            email="staff@example.com",
            password="Password123!",
            display_name="Staff Reviewer",
            is_staff=True,
        )

    @pytest.fixture
    def other_user(self) -> User:
        return User.objects.create_user(
            email="other@example.com",
            password="Password123!",
            display_name="Other User",
        )

    @pytest.fixture
    def passport(self, tenant_user: User) -> Passport:
        return Passport.objects.create(
            user=tenant_user,
            display_name="TenantPassport",
        )

    @pytest.fixture
    def sample_files(
        self,
    ) -> tuple[SimpleUploadedFile, SimpleUploadedFile, SimpleUploadedFile]:
        front = SimpleUploadedFile(
            "front.jpg", b"fake-front-bytes", content_type="image/jpeg"
        )
        back = SimpleUploadedFile(
            "back.jpg", b"fake-back-bytes", content_type="image/jpeg"
        )
        selfie = SimpleUploadedFile(
            "selfie.jpg", b"fake-selfie-bytes", content_type="image/jpeg"
        )
        return front, back, selfie

    def test_check_cooldown_inactive_when_no_rejections(
        self, passport: Passport
    ) -> None:
        cooldown = VerificationService.check_cooldown(passport)
        assert cooldown["cooldown_active"] is False
        assert cooldown["remaining_seconds"] == 0

    def test_check_cooldown_active_within_24_hours(
        self, passport: Passport, staff_user: User
    ) -> None:
        recent_time = timezone.now() - timedelta(hours=6)
        Verification.objects.create(
            passport=passport,
            state=Verification.State.REJECTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            reject_reason=RejectReason.ILLEGIBLE,
            submitted_at=recent_time - timedelta(hours=1),
            last_rejection_at=recent_time,
            reviewed_by=staff_user,
        )

        cooldown = VerificationService.check_cooldown(passport)
        assert cooldown["cooldown_active"] is True
        assert cooldown["remaining_seconds"] > 0
        assert cooldown["reject_reason"] == RejectReason.ILLEGIBLE
        assert cooldown["cooldown_until"] == recent_time + timedelta(hours=24)

    def test_check_cooldown_expired_after_24_hours(
        self, passport: Passport, staff_user: User
    ) -> None:
        past_time = timezone.now() - timedelta(hours=25)
        Verification.objects.create(
            passport=passport,
            state=Verification.State.REJECTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            reject_reason=RejectReason.EXPIRED,
            submitted_at=past_time - timedelta(hours=1),
            last_rejection_at=past_time,
            reviewed_by=staff_user,
        )

        cooldown = VerificationService.check_cooldown(passport)
        assert cooldown["cooldown_active"] is False
        assert cooldown["remaining_seconds"] == 0

    def test_submit_verification_forbidden_actor(
        self,
        passport: Passport,
        other_user: User,
        sample_files: tuple[SimpleUploadedFile, SimpleUploadedFile, SimpleUploadedFile],
    ) -> None:
        front, back, selfie = sample_files
        res = VerificationService.submit_verification(
            passport=passport,
            actor=other_user,
            nid_front_file=front,
            nid_back_file=back,
            selfie_file=selfie,
        )
        assert res["ok"] is False
        assert res["code"] == "forbidden_role"

    def test_submit_verification_cooldown_active(
        self,
        passport: Passport,
        tenant_user: User,
        staff_user: User,
        sample_files: tuple[SimpleUploadedFile, SimpleUploadedFile, SimpleUploadedFile],
    ) -> None:
        recent_time = timezone.now() - timedelta(hours=2)
        Verification.objects.create(
            passport=passport,
            state=Verification.State.REJECTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            reject_reason=RejectReason.ILLEGIBLE,
            submitted_at=recent_time - timedelta(hours=1),
            last_rejection_at=recent_time,
            reviewed_by=staff_user,
        )

        front, back, selfie = sample_files
        res = VerificationService.submit_verification(
            passport=passport,
            actor=tenant_user,
            nid_front_file=front,
            nid_back_file=back,
            selfie_file=selfie,
        )
        assert res["ok"] is False
        assert res["code"] == "cooldown_active"
        assert res["remaining_seconds"] > 0

    def test_submit_verification_invalid_files(
        self,
        passport: Passport,
        tenant_user: User,
    ) -> None:
        bad_file = SimpleUploadedFile("notes.txt", b"text", content_type="text/plain")
        res = VerificationService.submit_verification(
            passport=passport,
            actor=tenant_user,
            nid_front_file=bad_file,
            nid_back_file=bad_file,
            selfie_file=bad_file,
        )
        assert res["ok"] is False
        assert res["code"] == "invalid_files"

    def test_submit_verification_success(
        self,
        passport: Passport,
        tenant_user: User,
        sample_files: tuple[SimpleUploadedFile, SimpleUploadedFile, SimpleUploadedFile],
    ) -> None:
        front, back, selfie = sample_files
        res = VerificationService.submit_verification(
            passport=passport,
            actor=tenant_user,
            nid_front_file=front,
            nid_back_file=back,
            selfie_file=selfie,
        )
        assert res["ok"] is True
        verification = res["verification"]
        assert verification.state == Verification.State.SUBMITTED
        assert verification.passport == passport
        assert verification.nid_front_path.startswith("verifications/")

        # Passport status updated to PENDING
        passport.refresh_from_db()
        assert passport.status == Passport.Status.PENDING

        # Audit entry persisted
        audit_entry = AuditEntry.objects.filter(
            target_id=verification.pk, action="submit"
        ).first()
        assert audit_entry is not None
        assert audit_entry.actor_id == tenant_user.pk
        assert audit_entry.after_state["state"] == Verification.State.SUBMITTED

    def test_transition_forbidden_for_non_staff(
        self,
        passport: Passport,
        tenant_user: User,
    ) -> None:
        verification = Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=timezone.now(),
        )
        res = VerificationService.transition(
            verification=verification,
            new_state=Verification.State.VERIFIED,
            actor=tenant_user,
        )
        assert res["ok"] is False
        assert res["code"] == "forbidden_role"

    def test_transition_invalid_target_state(
        self,
        passport: Passport,
        staff_user: User,
    ) -> None:
        verification = Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=timezone.now(),
        )
        res = VerificationService.transition(
            verification=verification,
            new_state="nonexistent_state",
            actor=staff_user,
        )
        assert res["ok"] is False
        assert res["code"] == "invalid_state"

    def test_transition_illegal_dag_transition(
        self,
        passport: Passport,
        staff_user: User,
    ) -> None:
        # Verified cannot transition to Reviewing
        verification = Verification.objects.create(
            passport=passport,
            state=Verification.State.VERIFIED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=timezone.now(),
        )
        res = VerificationService.transition(
            verification=verification,
            new_state=Verification.State.REVIEWING,
            actor=staff_user,
        )
        assert res["ok"] is False
        assert res["code"] == "invalid_transition"

    def test_transition_rejection_missing_reason_code(
        self,
        passport: Passport,
        staff_user: User,
    ) -> None:
        verification = Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=timezone.now(),
        )
        res = VerificationService.transition(
            verification=verification,
            new_state=Verification.State.REJECTED,
            actor=staff_user,
            reason=None,
        )
        assert res["ok"] is False
        assert res["code"] == "missing_reason_code"

    def test_transition_rejection_invalid_reason_code(
        self,
        passport: Passport,
        staff_user: User,
    ) -> None:
        verification = Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=timezone.now(),
        )
        res = VerificationService.transition(
            verification=verification,
            new_state=Verification.State.REJECTED,
            actor=staff_user,
            reason="not_a_canonical_reason",
        )
        assert res["ok"] is False
        assert res["code"] == "invalid_reason_code"

    def test_transition_to_reviewing_success(
        self,
        passport: Passport,
        staff_user: User,
    ) -> None:
        verification = Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=timezone.now(),
        )
        res = VerificationService.transition(
            verification=verification,
            new_state=Verification.State.REVIEWING,
            actor=staff_user,
        )
        assert res["ok"] is True
        verification.refresh_from_db()
        assert verification.state == Verification.State.REVIEWING
        assert verification.reviewed_by == staff_user

        audit = AuditEntry.objects.filter(
            target_id=verification.pk, action="transition"
        ).first()
        assert audit is not None
        assert audit.after_state["state"] == Verification.State.REVIEWING

    def test_transition_to_verified_success_and_email(
        self,
        passport: Passport,
        staff_user: User,
        tenant_user: User,
    ) -> None:
        mail.outbox.clear()
        verification = Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=timezone.now(),
        )

        res = VerificationService.transition(
            verification=verification,
            new_state=Verification.State.VERIFIED,
            actor=staff_user,
        )
        assert res["ok"] is True
        verification.refresh_from_db()
        assert verification.state == Verification.State.VERIFIED
        assert verification.reviewed_at is not None
        assert verification.reviewed_by == staff_user

        passport.refresh_from_db()
        assert passport.status == Passport.Status.VERIFIED
        assert passport.is_verified is True

        # Email sent
        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert sent_email.to == [tenant_user.email]
        assert "Your Basha Pass Verification is Approved!" in sent_email.subject
        assert "Your Tenant Passport is now active!" in sent_email.body

    def test_transition_to_rejected_success_and_email(
        self,
        passport: Passport,
        staff_user: User,
        tenant_user: User,
    ) -> None:
        mail.outbox.clear()
        verification = Verification.objects.create(
            passport=passport,
            state=Verification.State.SUBMITTED,
            nid_front_path="p1",
            nid_back_path="p2",
            selfie_path="p3",
            submitted_at=timezone.now(),
        )

        res = VerificationService.transition(
            verification=verification,
            new_state=Verification.State.REJECTED,
            actor=staff_user,
            reason=RejectReason.ILLEGIBLE,
            notes="Please retake photo in better lighting.",
        )
        assert res["ok"] is True
        verification.refresh_from_db()
        assert verification.state == Verification.State.REJECTED
        assert verification.reject_reason == RejectReason.ILLEGIBLE
        assert verification.reviewer_notes == "Please retake photo in better lighting."
        assert verification.last_rejection_at is not None

        passport.refresh_from_db()
        assert passport.status == Passport.Status.REJECTED

        # Email sent
        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert sent_email.to == [tenant_user.email]
        assert "Basha Pass Verification Update" in sent_email.subject
        assert "Illegible Image" in sent_email.body
        assert "Please retake photo in better lighting." in sent_email.body
        assert "24-hour waiting period" in sent_email.body
