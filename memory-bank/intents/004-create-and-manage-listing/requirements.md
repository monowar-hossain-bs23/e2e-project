---
intent: 004-create-and-manage-listing
phase: inception
status: approved
created: '2026-10-31T06:50:00Z'
updated: '2026-10-31T07:35:00Z'
---

# Requirements: Create and Manage Listing

## Intent Overview

Enables verified tenants to create, edit, withdraw, and manage supply-side rental listings for available seats in a mess or private rooms in Dhaka. Governed by architectural constraints defined in `docs/ARCHITECTURE-SPINE.md` (AD-6 ListingService invariants, 3-active listing cap, photo upload validation, and 60-day auto-archive). Public feed browsing and multi-axis search filters are explicitly deferred to the subsequent intent.

## Business Goals

| Goal | Success Metric | Priority |
|------|----------------|----------|
| G-1: High-Trust Supply Inventory | 100% of created listings originate from passport-verified tenants. | Must |
| G-2: Spam & Abuse Prevention | Hard server-side enforcement of max 3 active listings per tenant. | Must |
| G-3: Accurate Lifestyle Matching | Full alignment of listing preference axes with tenant lifestyle dimensions. | Must |
| G-4: Effortless Self-Management | Authors can view, edit mutable terms, and withdraw listings in < 2 clicks. | Must |

---

## Functional Requirements

### FR-1: Verified Tenant Gate & Routing
- **Description**: Access to the listing creation interface (`/listings/create/`) is strictly restricted to authenticated users holding a verified Tenant Passport (`passport.status == 'verified'`).
- **Acceptance Criteria**:
  - If user is unauthenticated, redirect to `/accounts/login/?next=/listings/create/`.
  - If authenticated user has no passport or `status == 'unverified'`, redirect to `/passports/create/` with informational flash message: *"Please complete your Tenant Passport verification before posting a listing."*
  - If user passport `status == 'pending'`, redirect to `/dashboard/` with informational message: *"Your Tenant Passport is currently under review. You can create listings as soon as verification is approved."*
  - If user passport `status == 'rejected'`, redirect to `/dashboard/` displaying the rejection reason and waiting period status.
  - Only tenants with `passport.status == 'verified'` are permitted to access and submit the form.
- **Priority**: Must
- **Related Stories**: `017-listing-authorization-gate`

### FR-2: Active Listing Limit (3-Cap Rule)
- **Description**: A verified tenant can maintain at most 3 active (non-archived, non-withdrawn) listings simultaneously (PRD FR-12, AD-6).
- **Acceptance Criteria**:
  - `ListingService.create()` validates that `Listing.objects.filter(author=passport, archived_at__isnull=True, withdrawn_at__isnull=True).count() < 3`.
  - If the tenant already has 3 active listings:
    - The create view displays a prominent warning banner explaining the 3-listing cap and disables the form.
    - Direct POST submissions fail validation with error code `active_cap_reached` and message: *"You have reached the maximum limit of 3 active listings. Please archive or withdraw an existing listing to post a new one."*
- **Priority**: Must
- **Related Stories**: `018-listing-model-and-service-domain`

### FR-3: Listing Creation Form & Cross-Field Invariants
- **Description**: A multi-section listing form capturing accommodation details, rent, Dhaka location, preferred roommate lifestyles, descriptive notes, and photos.
- **Acceptance Criteria**:
  - **Kind**: Choice of `seat` (Seat in a room) or `room` (Private room).
  - **Rent**: Positive integer between ৳500 and ৳50,000 BDT.
  - **Rent Unit**: `per_seat` or `per_room`. Cross-field constraint enforced: if `kind == 'seat'`, `rent_unit` must be `per_seat`; if `kind == 'room'`, `rent_unit` must be `per_room`.
  - **Rent Period**: System-fixed to `per_month` (not user-editable in v1).
  - **Area**: Single selection from the 13 canonical Dhaka sub-areas (a room or seat is located in a single physical area).
  - **Roommate Lifestyle Preferences**:
    - `pref_gender`: `male`, `female`, `any`.
    - `pref_smoking`: `yes`, `no`, `any`.
    - `pref_sleep`: `early_bird`, `night_owl`, `flexible`.
    - `pref_occupation`: Multi-select from `student`, `garments_worker`, `private_job`, `freelancer`, `other`, `any`.
  - **Body Note**: Optional free-text note up to 500 characters, fully supporting Bengali and English Unicode characters.
- **Priority**: Must
- **Related Stories**: `018-listing-model-and-service-domain`, `020-listing-authoring-ui`

### FR-4: Listing Photo Upload & Storage
- **Description**: Tenants must upload at least 1 and at most 7 photos showcasing the accommodation.
- **Acceptance Criteria**:
  - Validates image file formats: JPEG, PNG, or WebP.
  - Validates file size: maximum 5 MB per photo.
  - Image files verified via magic bytes / Pillow to reject malicious payloads.
  - Stored at original upload resolution (no mandatory client/server cropping).
  - UI displays an advisory tip recommending a landscape 4:3 or 16:9 aspect ratio for optimal display.
  - Stored under public media directory `listings/photos/<listing_id>/`.
- **Priority**: Must
- **Related Stories**: `019-listing-photo-storage-service`, `020-listing-authoring-ui`

### FR-5: Lister Management Dashboard ("Your Listings")
- **Description**: Author-facing dashboard interface allowing tenants to view and manage all their listings (`/listings/mine/` or tab in `/dashboard/`).
- **Acceptance Criteria**:
  - Lists all listings authored by the authenticated tenant, sorted newest first.
  - Displays primary photo thumbnail, kind badge (Seat/Room), monthly rent with unit, sub-areas, and creation timestamp.
  - Status indicator: **Active** (green), **Withdrawn** (gray/muted), **Archived** (amber).
  - Filter toggle to switch between "Active" and "Show All / Archived".
  - Quick action buttons per listing: **Edit**, **Withdraw**, and **Preview**.
- **Priority**: Must
- **Related Stories**: `021-lister-management-dashboard`

### FR-6: Listing Edit Workflow & Locked Field Protection
- **Description**: Author can modify certain listing terms after publishing, while structural identity fields remain locked (AD-6).
- **Acceptance Criteria**:
  - **Mutable Fields**: `rent_bdt`, `rent_unit` (must maintain consistency with `kind`), `body` note, and photos (uploading new or deleting existing photos, maintaining 1–7 photo count).
  - **Locked Fields**: `kind` and `area` are immutable post-publish. Tampering attempts return error code `field_locked`.
  - Only the listing's author can access the edit view or execute updates. Unauthorized users receive 403 Forbidden.
- **Priority**: Must
- **Related Stories**: `022-listing-edit-and-lifecycle-actions`

### FR-7: Manual Listing Withdrawal
- **Description**: Lister can manually withdraw an active listing when the room/seat has been filled or is no longer available.
- **Acceptance Criteria**:
  - Author clicks "Withdraw Listing" with a confirmation modal.
  - Sets `withdrawn_at = timezone.now()`.
  - Withdrawn listings are immediately excluded from active inventory and no longer count toward the 3-active listing limit.
- **Priority**: Must
- **Related Stories**: `022-listing-edit-and-lifecycle-actions`

### FR-8: 60-Day Automatic Stale Archival
- **Description**: Listings older than 60 days automatically transition to archived status (FR-12, AD-6).
- **Acceptance Criteria**:
  - `ListingService.archive_stale()` queries listings where `archived_at IS NULL AND withdrawn_at IS NULL AND created_at < now() - 60 days` and stamps `archived_at = now()`.
  - Executable via a custom Django management command (`python manage.py archive_stale_listings`).
  - Archived listings no longer count toward the author's 3-active listing cap.
- **Priority**: Should
- **Related Stories**: `018-listing-model-and-service-domain`

---

## Non-Functional Requirements

### Performance & Storage
- Listing creation, update, and withdrawal operations complete within < 300ms (excluding network transmission time for photos).
- Image uploads streamed with chunked writing to prevent high memory usage.

### Security & Privacy
- **Strict Authorization**: Multi-tenant authorization check ensures only `author == request.user.passport` (or staff) can update or withdraw a listing.
- **Public Visibility**: Listing photos and descriptions are public assets, but author phone and email are never exposed through listing authoring endpoints (soft-gating occurs on the feed/detail view).

### Audit Trail
- All lifecycle events (creation, edits, manual withdrawal, and stale archival) are appended to the immutable `AuditEntry` log via `AuditService.append()` with actor attribution.
