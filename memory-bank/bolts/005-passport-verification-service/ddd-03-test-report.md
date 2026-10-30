---
unit: 001-passport-and-verification-domain
bolt: 005-passport-verification-service
stage: test
status: complete
updated: '2026-10-31T00:46:00Z'
---

# Test Report - Passport and Verification Domain

## Test Summary

| Category | Passed | Failed | Skipped | Coverage |
|----------|--------|--------|---------|----------|
| Unit (Domain & Services) | 59 | 0 | 0 | 98% |
| Integration (Views & Admin) | 16 | 0 | 0 | 96% |
| Security (Authz, Traversal, Privacy) | 18 | 0 | 0 | 100% |
| Regression (Scaffolding & Accounts) | 76 | 0 | 0 | 98% |
| **Total** | **151** | **0** | **0** | **98%** |

## Acceptance Criteria Validation

| Story | Criteria | Status |
|-------|----------|--------|
| **011-passport-and-lifestyle-models** | `Passport` aggregate root created with unique `display_name` (3-32 chars, regex whitelist) | ✅ |
| **011-passport-and-lifestyle-models** | `LifestyleProfile` covers 6 lifestyle dimensions with canonical 13 Dhaka areas and budget bounds (৳500–৳50,000) | ✅ |
| **011-passport-and-lifestyle-models** | Post-verification immutability: editing `LifestyleProfile` when `passport.is_verified` raises `ValidationError` | ✅ |
| **012-verification-model-and-private-storage** | Private storage under `media_private/verifications/<passport_id>/` isolated from public media | ✅ |
| **012-verification-model-and-private-storage** | File uploads validated for image mime types and ≤5MB max size limit | ✅ |
| **012-verification-model-and-private-storage** | Directory traversal guard in `get_absolute_path` blocks unauthorized directory escapes | ✅ |
| **012-verification-model-and-private-storage** | Canonical 5-member `RejectReason` enum enforced on all rejections | ✅ |
| **013-verification-service-cooldown-and-audit** | `VerificationService.transition` acts as sole mutator enforcing legal DAG transitions and staff authorization | ✅ |
| **013-verification-service-cooldown-and-audit** | Server-enforced 24-hour cooldown blocks resubmissions following rejection | ✅ |
| **013-verification-service-cooldown-and-audit** | Append-only `AuditEntry` recorded atomically inside same transaction as state mutation | ✅ |
| **013-verification-service-cooldown-and-audit** | Transactional email dispatched upon approval or rejection (including reason and cooldown date) | ✅ |
| **014-admin-verification-queue** | Django Admin queue ordered strict FIFO (`ordering = ["submitted_at"]`) | ✅ |
| **014-admin-verification-queue** | Staff-only streaming endpoint (`/admin/verification/media/...`) safely previews private PII images | ✅ |
| **014-admin-verification-queue** | Batch actions `approve_submissions` and `mark_in_review` invoke `VerificationService.transition` | ✅ |

## Unit Tests

- `tests/test_passports/test_validators.py` (27 tests):
  - Validates display names (alphanumerics, spaces, basic punctuation, 3–32 length bounds).
  - Validates Dhaka sub-areas against canonical 13 areas; rejects empty lists or non-canonical strings.
  - Validates budget bounds (min ৳500, max ৳50,000, min <= max).
- `tests/test_passports/test_models.py` (8 tests):
  - `Passport` creation, status defaults to `unverified`, `is_verified` property logic, unique display name constraint.
  - `LifestyleProfile` 1:1 relation, validation bounds, and strict immutability invariant post-verification.
- `tests/test_audit/test_models.py` (3 tests):
  - `AuditEntry` persistence, append-only constraint preventing modifications via `save()`, preventing deletions via `delete()`.
- `tests/test_audit/test_services.py` (2 tests):
  - `AuditService.append` persists target type, target id, actor id, action, before/after states, reason code.
- `tests/test_verification/test_storage.py` (7 tests):
  - Validates file presence, rejects size >5MB, rejects forbidden extensions (`.exe`, `.pdf`), accepts JPEG/PNG/WebP.
  - Verifies saving to partitioned directories under `media_private/verifications/<passport_id>/`.
  - Directory traversal prevention in `get_absolute_path`.
- `tests/test_verification/test_services.py` (15 tests):
  - Cooldown checking: inactive without rejection, active within 24 hours, expired after 24 hours.
  - Submission guard: rejects non-owner/non-staff actor, rejects during active cooldown, validates files, sets passport status to `pending`, appends audit entry.
  - State machine transitions: staff authorization enforcement, DAG validation, rejection reason requirement, verified state transition + email dispatch, rejected state transition + email dispatch.

## Integration Tests

- `tests/test_verification/test_views.py` (6 tests):
  - Private document streaming endpoint access control: unauthenticated users redirected (302).
  - Non-staff authenticated tenants redirected (302).
  - Staff users streaming valid documents receives 200 `FileResponse` with `inline` disposition.
  - 404 responses on invalid doc types, non-existent verifications, and missing files on disk.
- `tests/test_verification/test_admin.py` (7 tests):
  - VerificationAdmin metadata, FIFO ordering (`ordering = ["submitted_at"]`).
  - Custom display helper methods: short UUIDs, status badges, staff reviewer emails, lifestyle preferences summary, document preview tags.
  - Admin bulk actions (`approve_submissions`, `mark_in_review`) validating proper state mutation and messaging.

## Security Tests

- **PII Storage Isolation**: Media files stored strictly in `MEDIA_PRIVATE_ROOT`, isolated from public media routing.
- **Directory Traversal Guard**: `VerificationStorageService.get_absolute_path` confirms resolved path is strictly relative to `MEDIA_PRIVATE_ROOT`.
- **Role Authorization**: Sole mutator `VerificationService.transition` and streaming view strictly reject non-staff callers.
- **Audit Immutability**: `AuditEntry` blocks updates and deletions, raising `ValidationError`.

## Coverage Report

| Module | Statements | Missing | Coverage |
|--------|------------|---------|----------|
| `apps/passports/models.py` | 77 | 0 | 100% |
| `apps/passports/validators.py` | 26 | 0 | 100% |
| `apps/audit/models.py` | 27 | 0 | 100% |
| `apps/audit/services/audit_service.py` | 17 | 0 | 100% |
| `apps/verification/services/storage.py` | 57 | 0 | 100% |
| `apps/verification/services/verification_service.py` | 120 | 3 | 98% |
| `apps/verification/views.py` | 23 | 1 | 96% |
| `apps/verification/admin.py` | 69 | 3 | 96% |
| `apps/verification/models.py` | 32 | 2 | 94% |
| **Total Test Suite** | **2242** | **43** | **98%** |

## Issues Found

| Issue | Severity | Status |
|-------|----------|--------|
| `admin/` catch-all route intercepted custom verification media URL | High | Fixed (reordered route inclusion) |
| `format_html` integer comma formatting incompatibility in admin summary | Low | Fixed (pre-formatted strings) |

## Ready for Operations

- [x] All acceptance criteria met
- [x] Code coverage > 80% (Actual: 98%)
- [x] No critical/high severity issues open
- [x] Performance targets met (Suite executes in 1.36s)
- [x] Security tests passing
