---
id: 017-listing-and-photo-models
unit: 001-listing-domain-service
intent: 004-create-and-manage-listing
status: complete
priority: must
created: '2026-10-31T07:28:00Z'
assigned_bolt: 007-listing-domain-service
implemented: true
---

# Story: 017-listing-and-photo-models

## User Story

**As a** system architect
**I want** durable, normalized `Listing` and `ListingPhoto` models with UUIDv7 PKs and database-level constraints
**So that** accommodation posts maintain strict domain integrity, relational consistency, and time-ordered sortability

## Acceptance Criteria

- [x] **Given** a verified tenant passport, **When** creating a `Listing`, **Then** it generates a time-sortable UUIDv7 primary key, links to `author` (FK → `Passport.id`, ON DELETE RESTRICT), and validates `kind ∈ ('seat', 'room')`.
- [x] **Given** a listing payload, **When** validating rent fields, **Then** `rent_bdt` is bounded between ৳500 and ৳50,000, `rent_period` defaults to `'per_month'`, and `rent_unit` enforces cross-field consistency (`seat` ⇔ `per_seat`, `room` ⇔ `per_room`).
- [x] **Given** Dhaka sub-areas, **When** persisting `area`, **Then** it stores a PostgreSQL text array containing between 1 and 13 canonical Dhaka sub-areas.
- [x] **Given** lifestyle preferences, **When** saving a listing, **Then** `pref_gender`, `pref_smoking`, `pref_sleep`, and `pref_occupation` (array) choices are validated against canonical enums.
- [x] **Given** photos uploaded for a listing, **When** saving `ListingPhoto`, **Then** each photo record is linked via FK to `Listing` with an integer `order` index and image path.

## Technical Notes

- Matches schema specified in `docs/erd.md` §4 and `docs/ARCHITECTURE-SPINE.md` AD-6.
- Implements database CHECK constraints for rent range, kind, rent_unit, rent_period, and area cardinality.
- Indexes: `(author_id, archived_at, withdrawn_at)` for active-cap filtering; `(created_at DESC)` for chronological ordering.

## Dependencies

### Requires
- `011-passport-and-lifestyle-models` (`Passport` aggregate root)

### Enables
- `018-listing-service-and-active-cap`
- `019-listing-photo-storage-service`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| `rent_bdt` set to ৳400 or ৳60,000 | Validation error rejecting values outside [500, 50000]. |
| `kind='seat'` with `rent_unit='per_room'` | Validation error: cross-field constraint violated. |
| Non-canonical area passed | Validation error: only the 13 canonical Dhaka areas are accepted. |
