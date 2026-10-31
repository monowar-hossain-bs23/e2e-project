---
id: 020-verified-tenant-listing-gate
unit: 002-listing-authoring-and-management-ui
intent: 004-create-and-manage-listing
status: complete
priority: must
created: '2026-10-31T07:28:00Z'
assigned_bolt: 008-listing-management-ui
implemented: true
---

# Story: 020-verified-tenant-listing-gate

## User Story

**As a** platform moderator
**I want** a dedicated `VerifiedTenantRequiredMixin` guarding all listing creation and authoring views
**So that** unverified, unsubmitted, or pending users are guided smoothly to their next appropriate action instead of hitting abrupt access errors

## Acceptance Criteria

- [x] **Given** an unauthenticated visitor accessing `/listings/create/`, **When** the request arrives, **Then** redirect to `/accounts/login/?next=/listings/create/`.
- [x] **Given** an authenticated user without a passport or with `unverified` status, **When** visiting `/listings/create/`, **Then** redirect to `/passports/create/` with flash message: *"Please complete your Tenant Passport verification before posting a listing."*
- [x] **Given** an authenticated user whose passport status is `pending` (under staff review), **When** visiting `/listings/create/`, **Then** redirect to `/dashboard/` with flash message: *"Your Tenant Passport is currently under review. You can create listings as soon as verification is approved."*
- [x] **Given** an authenticated user whose passport was `rejected`, **When** visiting `/listings/create/`, **Then** redirect to `/dashboard/` displaying the rejection waiting period.
- [x] **Given** a user with `passport.status == 'verified'`, **When** visiting `/listings/create/`, **Then** allow full access to the listing creation interface.

## Technical Notes

- Reusable mixin implemented in `apps/listings/mixins.py` as `VerifiedTenantRequiredMixin(LoginRequiredMixin)`.
- Inspects `request.user.passport` and handles missing passport gracefully without Raising `AttributeError` or 500 errors.

## Dependencies

### Requires
- `001-passport-and-verification-domain`
- `015-passport-submission-wizard`

### Enables
- `021-listing-create-form-and-view`
- `022-lister-management-dashboard`
- `023-listing-edit-and-withdraw-views`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User has account but no passport record created yet | Treated as unverified, redirected to `/passports/create/`. |
| User verified passport, accesses `/listings/create/` | Permitted directly to creation view. |
