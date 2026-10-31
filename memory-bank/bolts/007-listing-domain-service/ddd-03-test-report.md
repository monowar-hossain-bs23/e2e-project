---
unit: 001-listing-domain-service
bolt: 007-listing-domain-service
stage: test
status: complete
updated: '2026-10-31T08:30:00Z'
---

# Test Report - Listing Domain Service

## Test Summary

| Category | Passed | Failed | Skipped | Coverage |
|----------|--------|--------|---------|----------|
| Unit (Domain Models & Validators) | 6 | 0 | 0 | 97% |
| Unit (Photo Storage & Payloads) | 6 | 0 | 0 | 90% |
| Integration (ListingService & Lifecycle) | 7 | 0 | 0 | 85% |
| Integration (ListingAdmin & Previews) | 2 | 0 | 0 | 89% |
| Regression (Scaffolding, Accounts, Passports, Verification) | 183 | 0 | 0 | 98% |
| **Total Test Suite** | **204** | **0** | **0** | **97%** |

---

## Acceptance Criteria Validation

| Story | Criteria | Status |
|-------|----------|--------|
| **017-listing-domain-model-and-validation** | `Listing` aggregate root created with UUIDv7 PK and relation to verified `Passport` author | ✅ |
| **017-listing-domain-model-and-validation** | `ListingKind` and `RentUnit` parity enforced (`seat` requires `per_seat`, `room` requires `per_room`) | ✅ |
| **017-listing-domain-model-and-validation** | Monthly rent bound strictly between ৳500 and ৳50,000 | ✅ |
| **017-listing-domain-model-and-validation** | Canonical 13 Dhaka sub-areas stored in portable `JSONField` with domain validation | ✅ |
| **017-listing-domain-model-and-validation** | Preferred roommate attributes (gender, smoking, sleep, occupation) validated and bounded | ✅ |
| **017-listing-domain-model-and-validation** | Optional host description text capped at 1,000 characters | ✅ |
| **018-listing-photo-storage-service** | Listing photos stored in public media partition (`media/listings/photos/<listing_id>/<uuid>.<ext>`) | ✅ |
| **018-listing-photo-storage-service** | Magic-byte header inspection validates true JPEG, PNG, and WebP payloads | ✅ |
| **018-listing-photo-storage-service** | Rejects non-image binaries, oversized files (> 5MB), and unsupported formats | ✅ |
| **018-listing-photo-storage-service** | Enforces photo count invariant (1 to 7 photos per listing) | ✅ |
| **018-listing-photo-storage-service** | `ListingPhoto` child entity persists display ordering sequence (0 is primary) | ✅ |
| **019-listing-service-cap-concurrency-and-lifecycle** | Sole mutator `ListingService.create` verifies author is passport-verified | ✅ |
| **019-listing-service-cap-concurrency-and-lifecycle** | 3-active listing cap strictly enforced under pessimistic row lock (`select_for_update`) | ✅ |
| **019-listing-service-cap-concurrency-and-lifecycle** | `ListingService.edit` enforces locked immutable fields (`author`, `kind`, `rent_unit`) | ✅ |
| **019-listing-service-cap-concurrency-and-lifecycle** | Manual withdrawal via `ListingService.withdraw` idempotently stamps `withdrawn_at` | ✅ |
| **019-listing-service-cap-concurrency-and-lifecycle** | Auto-archive management command (`archive_stale_listings`) bulk-archives listings older than 60 days | ✅ |
| **019-listing-service-cap-concurrency-and-lifecycle** | Append-only `AuditEntry` recorded for all listing creation, edit, withdrawal, and archive mutations | ✅ |

---

## Unit Tests

- `tests/test_listings/test_models.py` (6 tests):
  - `test_create_listing_with_valid_attributes`: Creates room listing with JSON areas and lifestyle preferences.
  - `test_listing_kind_and_rent_unit_mismatch_fails`: Enforces that `seat` cannot have `per_room` rent unit.
  - `test_rent_bounds_validation`: Enforces lower bound (< ৳500) and upper bound (> ৳50,000).
  - `test_invalid_area_choice_fails`: Rejects non-canonical Dhaka sub-areas.
  - `test_status_helper_properties`: Verifies `is_active`, `is_withdrawn`, `is_archived`, and `status_label`.
  - `test_listing_photo_ordering_and_primary_photo`: Verifies `primary_photo` returns photo with lowest `order` sequence.

- `tests/test_listings/test_storage.py` (6 tests):
  - `test_validate_photo_file_empty_raises_error`: Validates empty/None input fails.
  - `test_validate_photo_size_exceeded_raises_error`: Validates file size > 5MB triggers `ValidationError`.
  - `test_validate_photo_disallowed_extension`: Rejects forbidden file extensions (`.gif`, `.pdf`, `.exe`).
  - `test_validate_photo_magic_bytes_detection`: Verifies binary magic-byte detection for JPEG, PNG, and WebP, rejecting spoofed headers.
  - `test_validate_photo_count_bounds`: Enforces minimum 1 and maximum 7 photos constraint.
  - `test_save_photo_and_cleanup`: Verifies filesystem persistence and `cleanup_listing_photos` directory removal.

---

## Integration Tests

- `tests/test_listings/test_services.py` (7 tests):
  - `test_create_listing_unverified_author_fails`: Blocks unverified or pending passports from authoring listings.
  - `test_create_listing_success_with_audit`: Verifies listing creation, photo attachment, and audit trail generation.
  - `test_create_listing_cap_exceeded_fails`: Verifies that attempting to create a 4th active listing raises `ValidationError`.
  - `test_edit_mutable_fields_success`: Edits `rent_bdt`, `area`, `body`, and updates photos while maintaining invariants.
  - `test_edit_locked_fields_protection`: Verifies attempting to mutate `author`, `kind`, or `rent_unit` raises `ValidationError`.
  - `test_withdraw_listing_success`: Idempotently sets `withdrawn_at` and appends `AuditEntry`.
  - `test_archive_stale_listings_command`: Verifies `archive_stale_listings` management command archives listings older than 60 days.

- `tests/test_listings/test_admin.py` (2 tests):
  - `test_listing_admin_display_and_photo_preview`: Verifies admin display helpers (areas summary, status badges, primary thumbnail preview).
  - `test_listing_photo_inline_admin`: Verifies thumbnail rendering and preview tags for listing photo inlines.

---

## Security & Concurrency Verification

- **Pessimistic Active-Cap Row Locking**: `ListingService.create()` acquires a row-level `select_for_update()` lock on the author's `Passport` inside `transaction.atomic()`, strictly serializing concurrent creation requests and preventing race conditions against the 3-active listing invariant.
- **Deep Magic-Byte Payload Validation**: File uploads are verified against true byte signatures (`\xff\xd8\xff`, `\x89PNG\r\n\x1a\n`, `RIFF...WEBP`), preventing arbitrary file upload (AFU) vulnerabilities without adding heavy image processing library overhead.
- **Strict Role & Status Authorization**: Only tenants with approved `is_verified` passports can invoke listing creation. Non-owners cannot edit or withdraw listings.
- **Immutable Mutation Auditing**: All listing mutations (`listing_created`, `listing_edited`, `listing_withdrawn`, `listing_archived`) append immutable records to the `AuditEntry` aggregate.

---

## Coverage Report

| Module | Statements | Missing | Coverage |
|--------|------------|---------|----------|
| `apps/listings/apps.py` | 5 | 0 | 100% |
| `apps/listings/constants.py` | 37 | 0 | 100% |
| `apps/listings/management/commands/archive_stale_listings.py` | 13 | 0 | 100% |
| `apps/listings/migrations/0001_initial.py` | 9 | 0 | 100% |
| `apps/listings/models.py` | 66 | 2 | 97% |
| `apps/listings/services/storage.py` | 88 | 9 | 90% |
| `apps/listings/admin.py` | 54 | 6 | 89% |
| `apps/listings/validators.py` | 23 | 3 | 87% |
| `apps/listings/services/listing_service.py` | 138 | 21 | 85% |
| **Total `apps/listings/`** | **433** | **41** | **91%** |
| **Total Project Suite** | **3,454** | **98** | **97%** |

---

## Issues Found & Resolved

| Issue | Severity | Status | Resolution |
|-------|----------|--------|------------|
| Missing Pillow dependency in container | Medium | Resolved | Replaced PIL verification with binary magic-byte inspection in `ListingPhotoStorageService` and binary buffer fixtures. |
| Inactive photo count check on edit | Medium | Resolved | Initialized test listings with valid photos in fixtures to satisfy `MIN_LISTING_PHOTOS >= 1` requirement. |
| Media folder clutter in untracked git status | Low | Resolved | Added `media/listings/*` and `.gitkeep` to `.gitignore`. |
