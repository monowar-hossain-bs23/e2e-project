---
unit: 002-listing-authoring-and-management-ui
intent: 004-create-and-manage-listing
phase: construction
status: complete
created: '2026-10-31T07:25:00Z'
updated: '2026-10-31T10:25:00Z'
---

# Unit Brief: 002-listing-authoring-and-management-ui

## Purpose

Delivers the tenant-facing web interface for verified listing authoring, photo uploading, lister management dashboard, post-publish editing, and withdrawal. Enforces user authorization gates, provides clean responsive UI matching brand tokens, and guides listers with clear aspect ratio advice and cap limit warnings.

## Scope

### In Scope
- `VerifiedTenantRequiredMixin` guarding all listing authoring CBVs, redirecting unauthenticated, unverified, pending, or rejected users to appropriate surfaces with explanatory flash messages.
- `ListingCreationForm` and `ListingEditForm` supporting cross-field validation, Dhaka sub-area multi-select, lifestyle preferences, and multi-file photo uploads.
- `ListingCreateView`: multi-section creation form at `/listings/create/` with 3-active cap banner and photo uploader with landscape aspect-ratio recommendation.
- `ListerDashboardView`: "Your Listings" dashboard view (`/listings/mine/` or tab on `/dashboard/`) with Active, Withdrawn, and Archived status badges and filter toggle.
- `ListingEditView`: post-publish editing interface (`/listings/<uuid>/edit/`) allowing updates to rent, rent unit, body note, and photos while locking `kind` and `area`.
- `ListingWithdrawView`: manual withdrawal action (`/listings/<uuid>/withdraw/`) with modal confirmation and redirection to lister dashboard.
- Responsive HTML templates extending `base.html` using brand tokens, Bootstrap 5.3, and HTMX/Vanilla JS for photo preview handling.

### Out of Scope
- Public search feed, card grids, and search filters (Intent 005).
- Public listing detail view with soft-gated contact panel (Intent 005).
- Direct ORM operations (all updates flow through `ListingService`).

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Verified Tenant Gate & Routing | Must |
| FR-2 | Active Listing Limit (3-Cap Rule) UI Banner | Must |
| FR-3 | Listing Creation Form & Cross-Field Invariants | Must |
| FR-4 | Listing Photo Upload UI & Aspect Ratio Hint | Must |
| FR-5 | Lister Management Dashboard ("Your Listings") | Must |
| FR-6 | Listing Edit Workflow & Locked Field Protection | Must |
| FR-7 | Manual Listing Withdrawal Action & Modal | Must |

---

## Technical Architecture

- **Class-Based Views**: Built with Django `View` / `FormView` leveraging `LoginRequiredMixin` and `VerifiedTenantRequiredMixin`.
- **Forms**: Django `forms.ModelForm` or `forms.Form` with custom validation routines honoring cross-field invariants.
- **Templates**: `templates/listings/create.html`, `templates/listings/edit.html`, `templates/listings/mine.html`, and partial cards.
- **Styling**: `static/css/brand-tokens.css` and dedicated `static/css/listings.css`.
