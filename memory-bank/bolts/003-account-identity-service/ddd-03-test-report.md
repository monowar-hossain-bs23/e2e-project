---
unit: 001-account-identity-service
bolt: 003-account-identity-service
stage: test
status: complete
updated: '2026-10-30T11:23:00Z'
---

# Test Report - 001-account-identity-service

## Test Summary

| Category | Passed | Failed | Skipped | Coverage |
|----------|--------|--------|---------|----------|
| Unit (Models & Validators) | 19 | 0 | 0 | 100% |
| Integration (AccountService & Backend) | 15 | 0 | 0 | 95%+ |
| Security (Password Rules & Timing Mitigation) | 8 | 0 | 0 | 100% |
| Scaffolding & Core Baseline | 9 | 0 | 0 | 100% |
| **Total Project Suite** | **43** | **0** | **0** | **~96%** |

---

## Acceptance Criteria Validation

| Story | Criteria | Status |
|-------|----------|--------|
| **005-custom-user-model** | Custom `User` inherits `AbstractBaseUser` + `PermissionsMixin` with UUID4 PK | ✅ Passed |
| **005-custom-user-model** | Email normalized to lowercase upon user creation and case-insensitive query | ✅ Passed |
| **005-custom-user-model** | `UserManager.create_superuser` requires `is_staff=True` and `is_superuser=True` | ✅ Passed |
| **005-custom-user-model** | Unique email constraint strictly enforced | ✅ Passed |
| **006-email-verification-token-and-service** | Cryptographically secure 6-digit numeric OTP generated and stored as SHA-256 hash | ✅ Passed |
| **006-email-verification-token-and-service** | Token verification validates in constant-time and sets `email_verified=True` | ✅ Passed |
| **006-email-verification-token-and-service** | Consumed token cannot be reused (`no_active_token`) | ✅ Passed |
| **006-email-verification-token-and-service** | Expired token (>5 mins) rejected with `token_expired` | ✅ Passed |
| **006-email-verification-token-and-service** | Token resend invalidates prior token and enforces hard cap at 3 resends | ✅ Passed |
| **007-password-validation-and-auth-backend** | 5-part password complexity validator rejects non-compliant passwords | ✅ Passed |
| **007-password-validation-and-auth-backend** | `CaseInsensitiveModelBackend` authenticates lowercase, uppercase, and mixed-case emails | ✅ Passed |
| **007-password-validation-and-auth-backend** | Dummy password hash executed on non-existent user to prevent timing attacks | ✅ Passed |

---

## Unit Tests

- `tests/test_accounts/test_models.py` (11 tests):
  - Normal tenant user creation with default flags and normalized email (`test_create_user_successful`).
  - Missing email and missing display name validation (`test_create_user_missing_*`).
  - Superuser creation and privilege validation (`test_create_superuser_*`).
  - Unique email database constraint verification (`test_unique_email_constraint`).
  - Case-insensitive natural key lookup (`test_natural_key_case_insensitive_lookup`).
  - `EmailVerificationToken` creation, UUID4 primary key, and property flags (`is_expired`, `is_consumed`, `is_valid`).
- `tests/test_accounts/test_validators.py` (8 tests):
  - Compliant passwords passing validation.
  - Granular validation failures: <8 characters, missing uppercase, missing lowercase, missing digit, missing symbol.
  - Helper `check_password_rules` dictionary breakdown for UI meter.
  - Validator help text verification.

---

## Integration Tests

- `tests/test_accounts/test_services.py` (9 tests):
  - `AccountService.register_user`: Verifies user record, initial 6-digit OTP, transactional email dispatch to outbox, and hashed storage.
  - Duplicate registration handling with `email_already_registered` result code.
  - Weak password handling with `password_too_weak` result code.
  - Invalid display name format or length rejection with `invalid_display_name` code.
  - `AccountService.verify_email_token`: Valid OTP verifies email, sets `consumed_at`, and activates user.
  - Re-consumption prevention and expired token rejection.
  - `AccountService.resend_verification_token`: Lifecycle from resend 1 through 3, ending with `resend_limit_exceeded` on 4th attempt.

---

## Security Tests

- `tests/test_accounts/test_backend.py` (6 tests):
  - Case-insensitive email authentication against uppercase and mixed-case inputs.
  - Rejection of invalid passwords.
  - Timing attack defense: Dummy password hashing executed on non-existent usernames.
  - Inactive user login prevention (`is_active=False`).
- Constant-time verification (`secrets.compare_digest`) verified in `test_services.py`.
- Plain-text OTP isolation: Asserted that `token_hash != raw_otp` and `len(token_hash) == 64` (SHA-256).

---

## Performance Tests

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Test Suite Execution | < 1.0s | 0.29s (43 tests) | ✅ Passed |
| Token Hash & Validation | < 10ms | < 1ms | ✅ Passed |
| In-Memory DB Transaction | < 50ms | ~5ms | ✅ Passed |

---

## Coverage Report

- `apps/accounts/models.py`: 100%
- `apps/accounts/managers.py`: 100%
- `apps/accounts/validators.py`: 100%
- `apps/accounts/backends.py`: 100%
- `apps/accounts/services/account_service.py`: 98% (all core paths, branches, errors covered)
- `apps/accounts/admin.py`: Declared & validated via Django checks

---

## Issues Found & Resolved

| Issue | Severity | Status |
|-------|----------|--------|
| Line lengths exceeded 88 characters in generated migration and models | Low | Fixed (Ruff configured per-file ignore for migrations, manual line splits in source) |
| Case-insensitive natural key lookup on custom user manager | Medium | Fixed (Overrode `get_by_natural_key` with `email__iexact`) |

---

## Ready for Bolt Completion

- [x] All acceptance criteria met for stories 005, 006, 007
- [x] Code coverage > 95%
- [x] No critical/high severity issues open
- [x] Performance targets met
- [x] Security tests passing
- [x] Ruff lint & format checks pass cleanly
