---
id: 012-verification-model-and-private-storage
unit: 001-passport-and-verification-domain
intent: 003-tenant-passport-and-verification
status: complete
priority: must
created: '2026-10-30T13:40:00Z'
assigned_bolt: 005-passport-verification-service
implemented: true
---

# Story: 012-verification-model-and-private-storage

## User Story

**As a** system security architect,  
**I want** identity documents (NID front/back and selfie) stored in an isolated private storage backend with structured verification attempt records,  
**So that** sensitive citizen identity documents are completely inaccessible from public web URLs and strictly tracked per verification attempt.

## Acceptance Criteria

- [ ] **Given** a verification submission, **When** photos are saved, **Then** `VerificationStorageService` writes them to `media_private/` using a dedicated private storage backend that is never served by public static/media URLs (AD-9).
- [ ] **Given** a passport, **When** a verification attempt is created, **Then** `Verification` model records `passport_id`, `state` (`submitted`), `nid_front_path`, `nid_back_path`, `selfie_path`, `submitted_at`, and initializes `reject_reason` and `reviewed_by` as NULL.
- [ ] **Given** verification rejection reasons, **When** defined in code, **Then** they exist as a canonical 5-member Python `Enum` in `apps/verification/services/reject_reasons.py`: `expired`, `mismatch`, `illegible`, `tampering_suspected`, `other` (AD-4).
- [ ] **Given** an attempt by a non-staff user to download private NID media, **When** requested via HTTP, **Then** access is denied with HTTP 403 Forbidden.

## Technical Notes

- `Verification` model lives in `apps/verification/models.py`.
- `VerificationStorageService` lives in `apps/verification/services/storage.py` and isolates PII under `media_private/`.
- File constraints: JPEG, PNG, WebP up to 5 MB per file.

## Dependencies

### Requires
- `011-passport-and-lifestyle-models`

### Enables
- `013-verification-service-cooldown-and-audit`
- `014-admin-verification-queue`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| File size > 5 MB | File validation rejects upload before writing to storage |
| Unsupported file format (e.g. PDF/EXE) | Rejected by image format validator |
| Direct URL access to `media_private/` path | No web server route exists; 404 or 403 enforced |
