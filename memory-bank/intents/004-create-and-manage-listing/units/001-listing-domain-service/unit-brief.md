---
unit: 001-listing-domain-service
intent: 004-create-and-manage-listing
phase: construction
status: complete
created: '2026-10-31T07:25:00Z'
updated: '2026-10-31T10:25:00Z'
---

# Unit Brief: 001-listing-domain-service

## Purpose

Provides the domain aggregate root (`Listing`), child entities (`ListingPhoto`), file storage abstraction (`ListingPhotoStorageService`), and sole mutating service (`ListingService`) governing all supply-side accommodation inventory in Basha Pass. Strictly enforces invariants (AD-6), anti-abuse limits (FR-12), and audit compliance (AD-15).

## Scope

### In Scope
- `Listing` domain model with UUIDv7 PK, `author_id` referencing `Passport` (ON DELETE RESTRICT), kind enum (`seat`, `room`), rent fields (`rent_bdt`, `rent_unit`, `rent_period`), PostgreSQL text array for 13 Dhaka sub-areas, and 4 lifestyle preference axes.
- `ListingPhoto` child entity with order index, image file path, and cascade deletion.
- `ListingPhotoStorageService` managing public image persistence under `media/listings/photos/<listing_id>/` with MIME, extension, and magic byte validation (max 5MB each).
- `ListingService` encapsulating:
  - `create(...)`: verifies verified passport status, enforces `kind ↔ rent_unit` consistency, validates `rent_period == 'per_month'`, checks 3-active listing cap atomically, creates photos, and logs audit record.
  - `edit(...)`: allows mutating `rent_bdt`, `rent_unit`, `body`, and photos; blocks modification of `kind` and `area` with `field_locked`.
  - `withdraw(...)`: stamps `withdrawn_at = now()`.
  - `archive_stale()`: auto-archives active listings older than 60 days.
- Management command `archive_stale_listings`.
- Stock Django Admin registration for `Listing` and `ListingPhoto` with read-only invariant guards.

### Out of Scope
- Public search filtering and feed generation (`ListingFeedQuery` per AD-12 deferred to Intent 005).
- Visitor-facing HTML views, forms, and client-side photo upload scripts (handled by Unit 002).

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-2 | Active Listing Limit (3-Cap Rule) | Must |
| FR-3 | Listing Creation Form & Cross-Field Invariants | Must |
| FR-4 | Listing Photo Upload & Storage | Must |
| FR-6 | Listing Edit Workflow & Locked Field Protection | Must |
| FR-7 | Manual Listing Withdrawal | Must |
| FR-8 | 60-Day Automatic Stale Archival | Should |

---

## Domain Concepts

### Key Entities

| Entity | Description | Attributes |
|---|---|---|
| `Listing` | Aggregate root representing a supply-side room or mess seat post. | `id` (UUIDv7), `author_id` (FK → `Passport`), `kind` (`seat`/`room`), `rent_bdt`, `rent_unit`, `rent_period`, `area` (Array), `body`, `pref_gender`, `pref_smoking`, `pref_sleep`, `pref_occupation` (Array), `created_at`, `archived_at`, `withdrawn_at`. |
| `ListingPhoto` | Child entity representing an uploaded photo of the accommodation. | `id` (UUID), `listing` (FK), `photo_path` (CharField), `order` (PositiveSmallInteger), `created_at`. |

### Invariants & Business Rules
1. **Verified Status Precondition**: `author.status == Passport.Status.VERIFIED`.
2. **3-Active Cap**: At most 3 listings with `archived_at IS NULL AND withdrawn_at IS NULL` per author.
3. **Cross-Field Equality**: `kind == 'seat'` ⇔ `rent_unit == 'per_seat'`; `kind == 'room'` ⇔ `rent_unit == 'per_room'`.
4. **Immutable Fields**: `kind` and `area` cannot be modified after initial creation.
