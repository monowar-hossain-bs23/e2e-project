---
id: 023-listing-edit-and-withdraw-views
unit: 002-listing-authoring-and-management-ui
intent: 004-create-and-manage-listing
status: complete
priority: must
created: '2026-10-31T07:28:00Z'
assigned_bolt: 008-listing-management-ui
implemented: true
---

# Story: 023-listing-edit-and-withdraw-views

## User Story

**As a** listing author
**I want** to edit the rent terms, notes, and photos of my listing or withdraw it when filled
**So that** my post remains accurate without compromising immutable identity fields like area and kind

## Acceptance Criteria

- [x] **Given** an authored listing, **When** loading `/listings/<uuid>/edit/`, **Then** the form displays mutable fields (`rent_bdt`, `rent_unit`, `body`, photos) as editable, while `kind` and `area` are rendered as read-only display fields.
- [x] **Given** an edit submission, **When** valid changes are made, **Then** `ListingService.edit()` updates the listing, adds a flash message, and redirects to the lister dashboard.
- [x] **Given** an unauthorized user attempting to access `/listings/<uuid>/edit/`, **When** the request arrives, **Then** respond with HTTP 403 Forbidden.
- [x] **Given** an active listing, **When** author clicks "Withdraw Listing" and confirms in the modal, **Then** `ListingService.withdraw()` marks `withdrawn_at` and returns to the dashboard with a success message.
- [x] **Given** a withdrawn listing, **When** viewed on the dashboard, **Then** its status badge reflects "Withdrawn" and it is excluded from active caps.

## Technical Notes

- Views: `apps/listings/views.py::ListingEditView`, `ListingWithdrawView`.
- Form: `apps/listings/forms.py::ListingEditForm`.
- Template: `templates/listings/edit.html` with withdrawal confirmation modal.

## Dependencies

### Requires
- `018-listing-service-and-active-cap`
- `020-verified-tenant-listing-gate`
- `022-lister-management-dashboard`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Direct POST tampering attempting to alter `area` | Service rejects with `field_locked`. |
| Non-author sends POST to withdraw listing | 403 Forbidden returned, listing remains unchanged. |
