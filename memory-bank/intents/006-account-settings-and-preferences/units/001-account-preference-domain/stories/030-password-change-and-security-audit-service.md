---
story: 030-password-change-and-security-audit-service
unit: 001-account-preference-domain
intent: 006-account-settings-and-preferences
priority: Must
status: planned
created: '2026-11-01T11:45:00Z'
---

# Story 030: Password Change and Security Audit Service

## User Story

As an authenticated Basha Pass tenant,
I want to rotate my password securely from my account settings,
So that I can protect my account credentials while maintaining an immutable audit log of security events.

## Acceptance Criteria

- [ ] **Current Password Verification**: `AccountService.change_password(user, current_password, new_password)` verifies that `current_password` matches using `user.check_password()`; raises error if incorrect.
- [ ] **Complexity Enforcement**: `new_password` is validated against `PasswordComplexityValidator` (min 8 chars, uppercase, lowercase, numeric, special symbol).
- [ ] **Password Mutation**: Calling `user.set_password(new_password)` saves the newly hashed password.
- [ ] **Security Audit Trail**: Successful password rotation creates an append-only `AuditEntry` via `AuditService.append` with `action="password_changed"` and `actor_id=user.id` (zero raw password bytes in audit state).

## Technical Notes

- Wire into `apps/accounts/services/account_service.py`.
- Ensure unit tests verify bad current password rejection, weak new password rejection, correct hash update, and audit log generation.

## Dependencies

- Depends on `apps.accounts.validators.PasswordComplexityValidator` and `apps.audit.services.audit_service.AuditService`.
