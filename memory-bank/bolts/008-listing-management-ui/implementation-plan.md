---
stage: plan
bolt: 008-listing-management-ui
created: '2026-10-31T08:45:00Z'
---

## Implementation Plan: Listing Authoring & Management UI

### Objective

Deliver the complete user-facing presentation layer and management dashboard for Basha Pass accommodation listings. This bolt enables verified tenants to publish rooms/seats, preview photos with landscape aspect-ratio guidance, manage active listings within the 3-active cap, edit mutable terms with locked-field safety, and withdraw filled posts per PRD §4.4 and design mockups (`05-listing-create.html`, `02-dashboard-hub.html`).

---

### Stories Covered

- **020-verified-tenant-listing-gate**: Authorization mixin gating all authoring views, providing clear contextual redirects for unverified, pending, and rejected users.
- **021-listing-create-form-and-view**: Multi-section creation form at `/listings/create/`, client/server cross-validation, photo uploader with aspect-ratio guidance, and 3-active cap alert banner.
- **022-lister-management-dashboard**: "Your Listings" dashboard at `/listings/mine/` with tab filtering (Active vs Archived/Withdrawn), status badges, cap progress indicator, and quick actions.
- **023-listing-edit-and-withdraw-views**: Edit view at `/listings/<uuid>/edit/` preserving locked fields (`kind`, `area`), and manual withdrawal action at `/listings/<uuid>/withdraw/` with modal confirmation.

---

### Deliverables

1. **Authorization Gate Mixin** (`apps/listings/mixins.py`):
   - `VerifiedTenantRequiredMixin`: Subclasses `LoginRequiredMixin`.
   - Inspects `request.user.passport` status:
     - Unauthenticated → Redirect to `login` with `?next=`.
     - Missing passport or `unverified` → Redirect to `passport_create` with flash message.
     - `pending` review → Redirect to `dashboard` with informative review status flash message.
     - `rejected` → Redirect to `dashboard` with waiting period guidance.
     - `verified` → Permitted to access.

2. **Forms** (`apps/listings/forms.py`):
   - `ListingCreationForm`: Multi-field form for `kind`, `rent_bdt`, `rent_unit`, `area` (multi-select canonical Dhaka areas), `pref_gender`, `pref_smoking`, `pref_sleep`, `pref_occupation` (multi-select), `body`, and `photos` (multi-file input). Cross-validates kind/rent_unit parity, rent bounds (৳500–৳50,000), and 1–7 photo count.
   - `ListingEditForm`: Specialized edit form allowing mutation of `rent_bdt`, `rent_unit`, `body`, lifestyle preferences, and photo updates, while rendering `kind` and `area` as read-only.

3. **Views** (`apps/listings/views.py`):
   - `ListingCreateView`: Renders creation page; evaluates active listing count for current tenant; if at cap (3), renders warning banner and disables posting; invokes `ListingService.create()` on valid submission.
   - `ListerDashboardView`: "Your Listings" dashboard scoped strictly to `request.user.passport`; calculates cap progress (`N / 3 Active`); supports status tab filtering (`active` vs `inactive`).
   - `ListingEditView`: Validates object ownership (403 for non-owners); enforces locked fields; invokes `ListingService.edit()`.
   - `ListingWithdrawView`: Validates ownership (403 for non-owners); handles POST request to invoke `ListingService.withdraw()`.

4. **Templates & Static Assets**:
   - `templates/listings/create.html`: Responsive two-column authoring layout with form sections, photo dropzone, landscape advisory note (4:3 or 16:9), live preview card, and cap warning banner.
   - `templates/listings/mine.html`: Lister dashboard with cap meter, status badges, active/archived tabs, action buttons, empty state, and withdrawal modal.
   - `templates/listings/edit.html`: Edit form with locked identity fields callout and photo management.
   - `templates/listings/partials/`: Reusable partials for listing cards, status pills, and withdrawal modals.
   - `static/js/listing-photos.js`: Client-side drag-and-drop, photo preview grid, file size/extension validation, and aspect ratio guidance.

5. **Routing & Navigation**:
   - `apps/listings/urls.py`: Routes for `create/`, `mine/`, `<uuid:pk>/edit/`, and `<uuid:pk>/withdraw/`.
   - Include `listings.urls` in `config/urls.py`.
   - Update `templates/basha/partials/navbar.html` and verified dashboard (`templates/passports/dashboards/_verified.html`) to link to listing authoring and management.

6. **Automated Test Suite** (`tests/test_listings/test_views.py`):
   - Unit and integration tests covering all acceptance criteria across the 4 stories:
     - Gating mixin redirections and flash messages across all 5 user states.
     - Cap-reached banner and submission guard on `ListingCreateView`.
     - Valid creation flow with photo file uploads and audit entry creation.
     - Multi-tenant isolation and tab filtering on `ListerDashboardView`.
     - Locked-field immutability and ownership authorization on `ListingEditView`.
     - Modal withdrawal flow and 403 defenses on `ListingWithdrawView`.

---

### Dependencies

- **Bolt 007 (`007-listing-domain-service`)**: Provides `Listing`, `ListingPhoto`, `ListingService`, and `ListingPhotoStorageService`.
- **Unit 001 (`001-passport-and-verification-domain`)**: Provides `Passport` model and verification statuses (`verified`, `pending`, `unverified`, `rejected`).
- **Bootstrap 5 & Brand Tokens**: Uses existing CSS token palette (`brand-tokens.css`, `base.html`).

---

### Technical Approach

1. **Robust Ownership Defense**:
   - All object-specific views (`ListingEditView`, `ListingWithdrawView`) implement explicit `get_object()` checks verifying `listing.author == self.request.user.passport`, raising `PermissionDenied` (HTTP 403) on any mismatch.
2. **Safe Multi-File Upload Processing**:
   - The multi-photo selector uses standard Django `request.FILES.getlist('photos')` passed directly into `ListingService.create()` or `ListingService.edit()`, which validates magic-byte integrity and persists files via `ListingPhotoStorageService`.
3. **Graceful User Guidance (No Dead Ends)**:
   - Rather than returning raw 403 or 400 errors when an unverified or pending user attempts to create a listing, `VerifiedTenantRequiredMixin` issues informative Django flash messages and redirects them to the relevant action page (`/passports/create/` or `/dashboard/`).
4. **Client-Side Ergonomics with Server Invariants**:
   - `static/js/listing-photos.js` provides instant visual feedback for uploaded images, checks file size (<5MB) and type before upload, and displays a friendly notice for landscape aspect ratios (4:3 or 16:9). All client checks are strictly validated again on the backend.

---

### Acceptance Criteria Checklist

- [ ] **AC-1 (Gate Mixin)**: Anonymous redirected to login; unverified/no passport redirected to `/passports/create/` with flash message; pending/rejected redirected to `/dashboard/` with appropriate status messages; verified permitted.
- [ ] **AC-2 (Create View & Cap)**: Verified tenant at cap (3) sees warning banner and disabled submission; verified tenant under cap sees full creation form; landscape aspect-ratio note displayed in photo uploader; form submission persists listing and photos via `ListingService.create()`.
- [ ] **AC-3 (Lister Dashboard)**: `/listings/mine/` lists authored posts sorted newest first; tabs toggle between Active and Archived/Withdrawn; status badges and thumbnail previews render; empty state CTA displayed when 0 listings.
- [ ] **AC-4 (Edit & Locked Fields)**: `/listings/<uuid>/edit/` allows updating rent, preferences, host note, and photos; `kind` and `area` are read-only; non-owner access returns 403.
- [ ] **AC-5 (Withdraw Action)**: POST to `/listings/<uuid>/withdraw/` marks listing withdrawn via `ListingService.withdraw()`, excludes it from active cap, and redirects to dashboard with success message; non-owner attempt returns 403.
