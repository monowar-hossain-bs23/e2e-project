---
id: 024-listing-consent-service-and-projection
unit: 001-listing-feed-query-and-consent
intent: 005-public-listing-feed-and-search
status: ready
priority: must
created: '2026-10-31T16:00:00Z'
assigned_bolt: 009-listing-feed-query-and-consent
implemented: false
---

# Story: 024-listing-consent-service-and-projection

## User Story

**As a** verified lister
**I want** my direct contact info (email and phone) shielded by `ConsentService` and visible strictly to verified tenants
**So that** random anonymous internet visitors cannot harvest my personal contact details.

## Acceptance Criteria

- [ ] **Given** an unauthenticated viewer or unverified user, **When** `ConsentService.render(viewer, listing)` is invoked, **Then** the returned `ListingProjection` has `email=None`, `phone=None`, and `lifestyle_summary="Verify to see lifestyle fit"`.
- [ ] **Given** an authenticated user holding a verified Tenant Passport (`passport.status == 'verified'`), **When** `ConsentService.render(viewer, listing)` is invoked, **Then** the returned `ListingProjection` contains the lister's `email` and `phone` as well as the full author lifestyle summary.
- [ ] **Given** any viewer, **When** `ConsentService.render` constructs the projection, **Then** sensitive PII (author citizen ID number, NID photos, selfie) is never attached to the projection under any circumstances.
- [ ] **Given** an administrative viewer (`user.is_staff == True`), **When** `ConsentService.render` is called, **Then** an admin projection with PII is available for staff inspection only.

## Technical Notes

- Implements Architecture Spine AD-3 (`ConsentService` sole projection owner).
- `ListingProjection` should be an immutable dataclass or typed dictionary ensuring templates never access raw ORM instances directly.
- Handles viewer protocols: `AnonymousViewer`, `AuthenticatedViewer`, `StaffViewer`.

## Dependencies

### Requires
- `018-listing-service-and-active-cap` (Listing model)
- `012-passport-aggregate-and-state-machine` (Passport verification status)

### Enables
- `025-listing-feed-query-and-compatibility`
- `028-listing-detail-and-gated-contact-ui`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Author viewing their own listing | Full contact details rendered (author always sees own data) |
| Viewer with pending or rejected passport | Contact details redacted (`email=None`, `phone=None`) |
| Viewer with deleted/inactive account | Treated as anonymous viewer |

## Out of Scope

- Database query construction and filter handling (handled in Story `025`).
- Audit log persistence on page views (handled in Story `028`).
