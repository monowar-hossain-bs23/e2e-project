---
id: 022-lister-management-dashboard
unit: 002-listing-authoring-and-management-ui
intent: 004-create-and-manage-listing
status: complete
priority: must
created: '2026-10-31T07:28:00Z'
assigned_bolt: 008-listing-management-ui
implemented: true
---

# Story: 022-lister-management-dashboard

## User Story

**As a** verified tenant who posted listings
**I want** a dedicated "Your Listings" dashboard view
**So that** I can track the status of my active, withdrawn, and archived posts, monitor active caps, and take quick actions

## Acceptance Criteria

- [x] **Given** a verified tenant visiting `/listings/mine/`, **When** the page renders, **Then** all listings authored by the tenant are displayed sorted newest first.
- [x] **Given** active and inactive posts, **When** reviewing listings, **Then** each post displays a thumbnail, title/kind badge, rent per unit, sub-areas, and status badge (**Active**, **Withdrawn**, **Archived**).
- [x] **Given** the filter controls, **When** switching tabs between "Active (N)" and "Archived / Withdrawn", **Then** the view filters the listing cards accordingly.
- [x] **Given** an active listing card, **When** inspecting actions, **Then** "Edit" and "Withdraw" buttons are readily available.
- [x] **Given** zero authored listings, **When** viewing the page, **Then** an empty state displays an encouraging CTA: *"You haven't posted any listings yet. Post a room or seat to find verified roommates."*

## Technical Notes

- View: `apps/listings/views.py::ListerDashboardView`.
- Template: `templates/listings/mine.html` (aligned with `docs/mockups/02-dashboard-hub.html`).
- Queries: Filtered strictly by `author=request.user.passport`.

## Dependencies

### Requires
- `018-listing-service-and-active-cap`
- `020-verified-tenant-listing-gate`

### Enables
- `023-listing-edit-and-withdraw-views`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Tenant has 3 active listings | Header clearly shows `3/3 Active Listings` with CTA disabled or warning indicator. |
| User tries to view another tenant's `/listings/mine/` | Only request.user's own listings are queried (strict multi-tenant isolation). |
