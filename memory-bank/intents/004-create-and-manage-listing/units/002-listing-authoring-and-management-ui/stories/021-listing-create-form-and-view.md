---
id: 021-listing-create-form-and-view
unit: 002-listing-authoring-and-management-ui
intent: 004-create-and-manage-listing
status: complete
priority: must
created: '2026-10-31T07:28:00Z'
assigned_bolt: 008-listing-management-ui
implemented: true
---

# Story: 021-listing-create-form-and-view

## User Story

**As a** verified tenant with an available room or seat
**I want** a clear, intuitive listing creation form with photo previews, aspect ratio advice, and cap warnings
**So that** I can publish an attractive accommodation post in minutes while respecting platform rules

## Acceptance Criteria

- [x] **Given** a verified tenant at or above the 3-active listing cap, **When** loading `/listings/create/`, **Then** the page displays an active-cap warning banner and disables form submission.
- [x] **Given** a verified tenant under the cap, **When** loading the form, **Then** all inputs (kind, rent, rent unit, Dhaka areas, preferences, body note, photos) render cleanly with pre-styled Bootstrap/brand design tokens.
- [x] **Given** the photo upload area, **When** viewed, **Then** it presents an advisory notice recommending landscape photos (4:3 or 16:9 ratio) for optimal viewing.
- [x] **Given** invalid input (e.g. rent out of bounds, mismatched kind and rent unit, missing photos), **When** submitting, **Then** clean field-level error messages display inline without page crashes.
- [x] **Given** valid submission with 1–7 photos, **When** submitting, **Then** `ListingService.create()` persists the listing, adds a success flash message, and redirects to the lister dashboard.

## Technical Notes

- View: `apps/listings/views.py::ListingCreateView`.
- Form: `apps/listings/forms.py::ListingCreationForm`.
- Template: `templates/listings/create.html` (derived from `docs/mockups/05-listing-create.html`).
- JavaScript: `static/js/listing-photos.js` for client-side image preview and validation feedback before upload.

## Dependencies

### Requires
- `018-listing-service-and-active-cap`
- `019-listing-photo-storage-service`
- `020-verified-tenant-listing-gate`

### Enables
- `022-lister-management-dashboard`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User selects `seat` then tries to pick `per_room` | Client-side and server-side validation force `per_seat`. |
| User uploads 8 photos in multi-file selector | Form rejects upload before sending invalid batch. |
