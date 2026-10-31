---
id: 018-listing-service-and-active-cap
unit: 001-listing-domain-service
intent: 004-create-and-manage-listing
status: complete
priority: must
created: '2026-10-31T07:28:00Z'
assigned_bolt: 007-listing-domain-service
implemented: true
---

# Story: 018-listing-service-and-active-cap

## User Story

**As a** platform operator
**I want** `ListingService` to be the sole mutator governing listing lifecycle, 3-active cap enforcement, locked-field edits, and auto-archival
**So that** business invariants cannot be bypassed by any view, script, or admin path, and all mutations are captured in the audit log

## Acceptance Criteria

- [x] **Given** an unverified tenant, **When** invoking `ListingService.create()`, **Then** it rejects execution with code `unverified_author`.
- [x] **Given** a verified tenant with 3 active listings, **When** invoking `ListingService.create()`, **Then** it atomically detects the cap and rejects with code `active_cap_reached`.
- [x] **Given** valid listing parameters and photos, **When** invoking `ListingService.create()`, **Then** it creates the `Listing` and `ListingPhoto` records in a database transaction and logs an `AuditEntry` (`action='create'`).
- [x] **Given** an existing listing, **When** invoking `ListingService.edit()`, **Then** only `rent_bdt`, `rent_unit`, `body`, and photos can be changed; attempting to alter `kind` or `area` raises `field_locked`.
- [x] **Given** an active listing, **When** invoking `ListingService.withdraw()`, **Then** it sets `withdrawn_at = timezone.now()` and records an audit entry.
- [x] **Given** listings older than 60 days, **When** executing `ListingService.archive_stale()` or running `archive_stale_listings`, **Then** eligible listings have `archived_at` stamped and audit logs appended.

## Technical Notes

- Implements Architecture Spine AD-6 and AD-15.
- Concurrency protection on 3-active cap using `select_for_update()` inside `transaction.atomic()`.
- Provides Django management command `apps/listings/management/commands/archive_stale_listings.py`.

## Dependencies

### Requires
- `017-listing-and-photo-models`
- `013-verification-service-cooldown-and-audit` (`AuditService`)

### Enables
- `021-listing-create-form-and-view`
- `023-listing-edit-and-withdraw-views`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Concurrent creation attempts by same author at cap 2 | Second transaction serialized and blocked at cap 3. |
| Lister attempts to edit `area` or `kind` | Blocked with `{ok: False, code: 'field_locked'}`. |
| Withdrawing an already withdrawn listing | Idempotent operation, returns existing state without error. |
