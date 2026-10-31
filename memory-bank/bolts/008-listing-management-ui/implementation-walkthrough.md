---
stage: implement
bolt: 008-listing-management-ui
status: complete
updated: '2026-10-31T09:05:00Z'
---

# Implementation Walkthrough: Listing Authoring & Management UI

## Overview

In Stage 2 of **Bolt 008 (`008-listing-management-ui`)**, we built the complete presentation and authoring layer for Basha Pass accommodation listings. This equips verified tenants with intuitive, responsive interfaces to create, manage, edit, and withdraw room and seat posts within platform guidelines (such as the 3-active listing cap and locked identity fields).

---

## Implemented Components & Files

### 1. Authorization Gatekeeper Mixin
- **File**: `apps/listings/mixins.py`
- **Class**: `VerifiedTenantRequiredMixin(LoginRequiredMixin)`
- **Behavior**:
  - `AnonymousUser` → Redirects to `login` with `?next=`.
  - Unsubmitted / `unverified` passport → Redirects to `/passports/create/` with flash warning: *"Please complete your Tenant Passport verification before posting a listing."*
  - `pending` verification → Redirects to `/dashboard/` with flash info: *"Your Tenant Passport is currently under review. You can create listings as soon as verification is approved."*
  - `rejected` verification → Redirects to `/dashboard/` with flash warning to observe the waiting period.
  - `verified` passport → Grants access.

### 2. Listing Forms & Multiple File Widget
- **File**: `apps/listings/forms.py`
- **Classes**:
  - `MultipleFileInput(forms.FileInput)`: HTML5 multiple-file input with `allow_multiple_selected = True`.
  - `ListingCreationForm`: Multi-field form validating `kind`, `rent_bdt` (৳500–৳50,000), `rent_unit` (enforcing parity with `kind`), canonical Dhaka sub-areas, lifestyle preferences, optional body text, and 1 to 7 photos via `ListingPhotoStorageService.validate_photo_file`.
  - `ListingEditForm`: Specialized edit form allowing updates to rent terms, preferences, host notes, and additional photos while strictly guarding immutable fields (`kind`, `area`).

### 3. Class-Based Views & Security Enforcements
- **File**: `apps/listings/views.py`
- **Classes**:
  - `ListingCreateView`: Evaluates active listing count against `MAX_ACTIVE_LISTINGS_PER_USER` (3). If cap is reached, renders alert banner and blocks form submission. On valid POST, invokes `ListingService.create()`.
  - `ListerDashboardView`: Scoped strictly to `request.user.passport` (preventing multi-tenant leakage). Calculates cap progress, renders Active vs Archived/Withdrawn tabs, and displays accommodation cards.
  - `ListingEditView`: Validates author ownership via `get_object()` (raising 403 `PermissionDenied` for non-owners). Invokes `ListingService.edit()`.
  - `ListingWithdrawView`: Validates author ownership (403 for non-owners). Handles POST to invoke `ListingService.withdraw()` idempotently.

### 4. Client-Side Photos & Live Preview Script
- **File**: `static/js/listing-photos.js`
- **Features**:
  - Drag-and-drop & file browser integration.
  - Dynamic thumbnail preview gallery with "Primary" badge on first image.
  - Client-side size (< 5MB) and count (1–7) checks.
  - Natural image dimension inspection showing advisory alert if non-landscape photos are detected.
  - Real-time synchronization of sticky live preview card as the user updates price, unit, kind, areas, or description.

### 5. Responsive Templates & Partials
- `templates/listings/create.html`: Styled with `static/css/listings.css` matching Mockup 05 (`05-listing-create.html`), including `navbar.html`, `bp-page-head`, `bp-status-pill`, `bp-section-card`, `bp-chipgroup`, photo dropzone, and sticky feed preview card.
- `templates/listings/mine.html`: Lister dashboard with `navbar.html`, active cap meter, toggle tabs, accommodation card list, empty state, and withdrawal modal.
- `templates/listings/edit.html`: Edit form with `navbar.html`, locked identity fields (`kind`, `area`) explanation, editable pricing/preferences, and photo management.
- `templates/listings/partials/listing_card.html`: Reusable card matching mockup design tokens, status badges, price, and actions.
- `templates/listings/partials/withdraw_modal.html`: Confirmation modal for withdrawal.
- `templates/basha/partials/navbar.html`: Links to "Your Listings" and "Post a listing" for verified tenants.
- `templates/passports/dashboards/_verified.html`: "Post Accommodation" and "Your Listings" quick CTAs; duplicate profile fields removed in favor of upper `passport_header.html`.
- `static/css/listings.css`: Dedicated styling extracted directly from mockup 05.
- `static/css/brand-tokens.css`: Added `.btn-outline-primary` mapped to `--bp-primary` (Trust Teal).

### 6. URL Routing
- **File**: `apps/listings/urls.py`
  - `/listings/create/` (`listing_create`)
  - `/listings/mine/` (`listing_mine`)
  - `/listings/<uuid:pk>/edit/` (`listing_edit`)
  - `/listings/<uuid:pk>/withdraw/` (`listing_withdraw`)
- **File**: `config/urls.py`: Included under `path("listings/", include("apps.listings.urls"))`.

---

## Quality & Style Verification

- **Linting & Formatting**: `poetry run ruff check .` and `poetry run ruff format --check .` ran cleanly across 107 files with zero errors.
- **Regression Testing**: All 204 existing unit and integration tests continue to pass in 0.96s.
