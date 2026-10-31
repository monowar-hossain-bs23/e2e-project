---
intent: 004-create-and-manage-listing
phase: inception
status: units-decomposed
updated: '2026-10-31T07:22:00Z'
---

# 004-create-and-manage-listing - Unit Decomposition

## Units Overview

This intent decomposes into 2 distinct units of work, cleanly separating domain models and service invariants from presentation views and user dashboards:

### Unit 1: `001-listing-domain-service`

**Description**: Core domain entities, storage service, lifecycle mutators, and administrative invariants for the supply-side listing catalog. Enforces PRD FR-10/FR-12, ERD §4, and Architecture Spine AD-6, AD-9, AD-15.

**Stories**:
- `017-listing-and-photo-models`: `Listing` & `ListingPhoto` domain models with UUIDv7 PKs, 13 canonical Dhaka areas, cross-field constraints, and lifestyle preference axes.
- `018-listing-service-and-active-cap`: `ListingService` sole mutator for creation, 3-active cap check, immutable field protection, manual withdrawal, 60-day auto-archive, and audit logging.
- `019-listing-photo-storage-service`: `ListingPhotoStorageService` validating 1–7 photos (JPEG/PNG/WebP, ≤5MB, magic bytes/Pillow) and managing public media persistence.

**Deliverables**:
- `apps/listings/models.py` (`Listing`, `ListingPhoto`)
- `apps/listings/services/listing_service.py` (`ListingService`)
- `apps/listings/services/storage.py` (`ListingPhotoStorageService`)
- `apps/listings/management/commands/archive_stale_listings.py`
- `apps/listings/admin.py` (stock Django admin integration)
- Automated unit & integration tests (`tests/test_listings/`)

**Dependencies**:
- Depends on: `001-account-identity-service` (Custom User), `001-passport-and-verification-domain` (`Passport`, `LifestyleProfile`), `apps.audit` (`AuditService`)
- Depended by: `002-listing-authoring-and-management-ui`

**Estimated Complexity**: L (Large — strict domain invariants, transaction safety, photo storage)

---

### Unit 2: `002-listing-authoring-and-management-ui`

**Description**: Tenant-facing presentation layer for verified listing authoring and self-management. Realizes user journeys UJ-1, UJ-2, and mockup designs (05-listing-create, dashboard hub).

**Stories**:
- `020-verified-tenant-listing-gate`: Authorization guard mixin enforcing `passport.status == 'verified'`, redirecting unverified or pending users with clear instructional guidance.
- `021-listing-create-form-and-view`: Multi-section listing creation view with form validation, photo uploader with aspect-ratio advisory note, and active cap banner.
- `022-lister-management-dashboard`: "Your Listings" dashboard view showing authored listings with status badges (Active, Withdrawn, Archived) and filter toggle.
- `023-listing-edit-and-withdraw-views`: Edit view for mutable terms (`rent_bdt`, `rent_unit`, `body`, photos) and manual withdrawal action with confirmation modal.

**Deliverables**:
- `apps/listings/views.py` (`ListingCreateView`, `ListerDashboardView`, `ListingEditView`, `ListingWithdrawView`)
- `apps/listings/forms.py` (`ListingCreationForm`, `ListingEditForm`)
- `templates/listings/create.html`, `templates/listings/edit.html`, `templates/listings/mine.html`
- Static CSS / JS for photo preview and delete handling (`static/js/listing-photos.js`)
- Automated view & template tests (`tests/test_listings/test_views.py`)

**Dependencies**:
- Depends on: `001-listing-domain-service`, `002-passport-verification-ui` (Base templates, brand tokens)
- Depended by: Public Listing Feed & Filter (Intent 005)

**Estimated Complexity**: M (Medium — form validation, multi-photo UI, dashboard tabs)

---

## Unit Dependency Graph

```text
[001-passport-and-verification-domain] ───┐
                                          ▼
                         [001-listing-domain-service]
                                          │
                                          ▼
                   [002-listing-authoring-and-management-ui]
```

## Execution Order

1. **Bolt 007**: `001-listing-domain-service` (Foundation domain, models, services, storage, and tests via DDD bolt)
2. **Bolt 008**: `002-listing-authoring-and-management-ui` (Gated CBVs, forms, author dashboard, edit/withdraw UI)
