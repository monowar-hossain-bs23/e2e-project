---
id: 013-verification-service-cooldown-and-audit
unit: 001-passport-and-verification-domain
intent: 003-tenant-passport-and-verification
status: ready
priority: must
created: '2026-10-30T13:40:00Z'
assigned_bolt: 005-passport-verification-service
implemented: false
---

# Story: 013-verification-service-cooldown-and-audit

## User Story

**As a** system operator,  
**I want** verification state mutations strictly controlled by `VerificationService` with 24-hour rejection cooldown, transactional audit logging, and direct email delivery,  
**So that** verification integrity is maintained, spam resubmissions are blocked, and all staff decisions are durably audited.

## Acceptance Criteria

- [ ] **Given** any verification state transition, **When** requested, **Then** `VerificationService.transition(...)` is the sole callable mutator, enforcing legality of state changes (`submitted` → `reviewing` → `verified` / `rejected`) (AD-2).
- [ ] **Given** a state transition attempt, **When** evaluated, **Then** role authorization is strictly enforced: `actor` must be passport owner for `submit`/`resubmit`, and `is_staff=True` for `reviewing`/`verified`/`rejected`.
- [ ] **Given** a rejected passport, **When** resubmission is attempted before 24 hours have elapsed since `last_rejection_at`, **Then** `VerificationService` blocks resubmission with `{ok: false, code: "cooldown_active", remaining_seconds: ...}` (FR-9).
- [ ] **Given** any state mutation, **When** executed, **Then** `AuditService.append(...)` writes an append-only `AuditEntry` within the same database transaction capturing `actor_id`, `target_id`, `before_state`, `after_state`, and `reason_code` (AD-15).
- [ ] **Given** a transition to `verified` or `rejected`, **When** committed, **Then** `VerificationService` dispatches an immediate email notification within 5 minutes containing the decision and next steps (FR-18, AD-7).

## Technical Notes

- Implemented in `apps/verification/services/verification_service.py` and `apps/audit/services/audit_service.py`.
- `AuditEntry` model in `apps/audit/models.py` uses polymorphic `target_type` + `target_id`.
- Rejection email renders the human-readable description of the selected `RejectReason` enum member.

## Dependencies

### Requires
- `012-verification-model-and-private-storage`

### Enables
- `014-admin-verification-queue`
- `016-verification-status-dashboards`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Resubmission at 23 hours 59 minutes | Rejected; cooldown active until full 24 hours have passed |
| Non-staff user calls verify transition | Forbidden; returns `{ok: false, code: "forbidden_role"}` |
| Invalid transition (e.g. `submitted` → `verified` skipping `reviewing`) | Rejected with `{ok: false, code: "invalid_transition"}` |
| Email delivery failure | Service logs failure and does not abort atomic database transaction |
