---
stage: test
bolt: 008-listing-management-ui
status: complete
updated: '2026-10-31T10:15:00Z'
---

# Test Walkthrough: Listing Authoring & Management UI

## Test Summary

| Category | Passed | Failed | Skipped | Coverage |
|----------|--------|--------|---------|----------|
| Unit (Forms & Mixins) | 6 | 0 | 0 | 88% |
| Integration (Views & Lifecycle) | 15 | 0 | 0 | 94% |
| Security (Authz, Multi-Tenant, Locked Fields) | 21 | 0 | 0 | 100% |
| Regression (Scaffolding, Accounts, Passports, Verification) | 183 | 0 | 0 | 98% |
| **Total Test Suite** | **225** | **0** | **0** | **97%** |

---

## Acceptance Criteria Validation

| Story | Criteria | Status |
|-------|----------|--------|
| **020-verified-tenant-listing-gate** | Anonymous visitor to `/listings/create/` redirected to login with `?next=` | ✅ |
| **020-verified-tenant-listing-gate** | Authenticated user with no passport or unverified redirected to `/passports/create/` with instructional flash message | ✅ |
| **020-verified-tenant-listing-gate** | Authenticated user with `pending` review redirected to `/dashboard/` with review status flash message | ✅ |
| **020-verified-tenant-listing-gate** | Authenticated user with `rejected` passport redirected to `/dashboard/` displaying waiting period message | ✅ |
| **020-verified-tenant-listing-gate** | User with verified passport granted 200 OK access to `/listings/create/` and `/listings/mine/` | ✅ |
| **021-listing-create-form-and-view** | Verified tenant under cap sees creation form with dropzone and landscape aspect ratio advisory notice | ✅ |
| **021-listing-create-form-and-view** | Verified tenant at cap (3 active) sees high-contrast warning banner and disabled submission button | ✅ |
| **021-listing-create-form-and-view** | POST at active cap rejected with flash error and redirected to `/listings/mine/` | ✅ |
| **021-listing-create-form-and-view** | Form validation catches rent bounds (৳500–৳50,000), kind/unit parity mismatch, and missing photos | ✅ |
| **021-listing-create-form-and-view** | Valid creation with 1–7 photos persists `Listing` and redirects to `/listings/mine/` with success message | ✅ |
| **022-lister-management-dashboard** | `/listings/mine/` lists authored posts sorted newest first with status badges and thumbnails | ✅ |
| **022-lister-management-dashboard** | Strict multi-tenant isolation: other users' listings never leak into current user's dashboard | ✅ |
| **022-lister-management-dashboard** | Tab filtering: `?tab=active` shows active posts; `?tab=inactive` shows withdrawn and archived posts | ✅ |
| **022-lister-management-dashboard** | Empty state card renders CTA: *"Post Your First Listing"* when active listing count is 0 | ✅ |
| **023-listing-edit-and-withdraw-views** | Author accessing `/listings/<uuid>/edit/` sees locked fields (`kind`, `area`) as read-only | ✅ |
| **023-listing-edit-and-withdraw-views** | Non-author accessing `/listings/<uuid>/edit/` receives HTTP 403 Forbidden | ✅ |
| **023-listing-edit-and-withdraw-views** | Valid edit updates `rent_bdt`, `body`, and preferences while preserving immutable fields | ✅ |
| **023-listing-edit-and-withdraw-views** | Non-author POST to `/listings/<uuid>/withdraw/` returns HTTP 403 Forbidden | ✅ |
| **023-listing-edit-and-withdraw-views** | Author POST to `/listings/<uuid>/withdraw/` marks `withdrawn_at`, frees up active cap slot, and redirects | ✅ |

---

## Test Execution Details

- `tests/test_listings/test_views.py` (21 tests, 0.42s):
  - `TestVerifiedTenantRequiredMixin` (6 tests):
    - `test_anonymous_user_redirected_to_login`
    - `test_authenticated_no_passport_redirects_to_passport_create`
    - `test_authenticated_unverified_passport_redirects_to_passport_create`
    - `test_authenticated_pending_passport_redirects_to_dashboard`
    - `test_authenticated_rejected_passport_redirects_to_dashboard`
    - `test_authenticated_verified_passport_allowed`
  - `TestListingCreateView` (5 tests):
    - `test_get_create_view_under_cap`
    - `test_get_create_view_at_cap`
    - `test_post_create_view_at_cap_blocked`
    - `test_post_create_view_validation_error_mismatched_kind_unit`
    - `test_post_create_view_validation_error_missing_photos`
    - `test_post_create_view_success`
  - `TestListerDashboardView` (3 tests):
    - `test_dashboard_empty_state`
    - `test_dashboard_multi_tenant_isolation`
    - `test_dashboard_tab_filtering_active_vs_inactive`
  - `TestListingEditView` (3 tests):
    - `test_edit_view_get_owner_allowed`
    - `test_edit_view_get_non_owner_forbidden`
    - `test_edit_view_post_updates_mutable_fields`
  - `TestListingWithdrawView` (3 tests):
    - `test_withdraw_get_redirects_to_mine`
    - `test_withdraw_post_non_owner_forbidden`
    - `test_withdraw_post_owner_success`

---

## User Polish Items Verified

1. **Dashboard Passport Redundancy Fixed**:
   - Redundant profile attribute rows removed from `_verified.html`.
   - Upper `passport_header.html` enriched with area preference pills, preserving clean hierarchy and passing all regression assertions.
2. **Brand Theme Colors on Buttons**:
   - Added `.btn-outline-primary` to `static/css/brand-tokens.css` with `--bp-primary` (`#0F6E7A` Trust Teal) and active/hover states, replacing Bootstrap's default generic blue.
3. **Navbar & Layout Consistency**:
   - Included `navbar.html` across `create.html`, `mine.html`, and `edit.html`.
   - Added "Your Listings" and "Post a listing" links in navbar for verified tenants.
4. **Mockup 05 Authenticity**:
   - Created `static/css/listings.css` implementing `.bp-page-head`, `.bp-status-pill`, `.bp-section-card`, `.bp-chipgroup`, `.bp-upload`, and `.bp-preview`.

---

## Coverage Metrics

| Module | Statements | Missing | Coverage |
|--------|------------|---------|----------|
| `apps/listings/apps.py` | 5 | 0 | 100% |
| `apps/listings/constants.py` | 37 | 0 | 100% |
| `apps/listings/urls.py` | 3 | 0 | 100% |
| `apps/listings/management/commands/archive_stale_listings.py` | 13 | 0 | 100% |
| `apps/listings/migrations/0001_initial.py` | 9 | 0 | 100% |
| `apps/listings/models.py` | 66 | 2 | 97% |
| `apps/listings/views.py` | 100 | 6 | 94% |
| `apps/listings/services/storage.py` | 88 | 9 | 90% |
| `apps/listings/admin.py` | 54 | 6 | 89% |
| `apps/listings/mixins.py` | 32 | 4 | 88% |
| `apps/listings/validators.py` | 23 | 3 | 87% |
| `apps/listings/services/listing_service.py` | 138 | 20 | 86% |
| `apps/listings/forms.py` | 80 | 12 | 85% |
| **Total `apps/listings/`** | **648** | **62** | **90%** |
| **Total Project Test Suite** | **3,905** | **119** | **97%** |
