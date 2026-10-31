---
id: 026-feed-view-and-filter-ui
unit: 002-listing-feed-and-detail-ui
intent: 005-public-listing-feed-and-search
status: ready
priority: must
created: '2026-10-31T16:00:00Z'
assigned_bolt: 010-listing-discovery-and-detail-ui
implemented: false
---

# Story: 026-feed-view-and-filter-ui

## User Story

**As a** prospective seeker
**I want** to browse the public listing feed with an offcanvas filter drawer and sorting menu
**So that** I can easily refine listings by Dhaka areas, budget, accommodation kind, and roommate habits.

## Acceptance Criteria

- [ ] **Given** any visitor visiting `/listings/` (or `/browse/`), **When** the page loads, **Then** the listing feed renders with top navigation, page header, result count bar, filter trigger button, sort dropdown, and a 3-column responsive card grid matching [Mockup 03](file:///home/bs01496/Documents/LMS/basa-pass/docs/mockups/03-listing-feed.html).
- [ ] **Given** the filter trigger button is clicked, **When** the drawer opens, **Then** the offcanvas sidebar renders chip groups for Area (13 Dhaka areas), accommodation kind (`Seat` / `Room`), rent unit, budget range slider (৳500–৳50,000), preferred gender, smoking, sleep schedule, and occupation.
- [ ] **Given** filters are selected and applied, **When** the form submits, **Then** the URL updates with query parameters and the feed updates to show matching listings.
- [ ] **Given** active filters are applied, **When** the result bar renders, **Then** the filter button displays a badge pill showing the count of active filters, and the drawer footer features a "Clear all" link that resets filters.
- [ ] **Given** a sort option is selected (`Newest first`, `Rent: Low to high`, `Rent: High to low`), **When** the feed refreshes, **Then** the selected sort order is applied and reflected in the UI dropdown.
- [ ] **Given** a query that matches 0 listings, **When** the page renders, **Then** a friendly empty state is displayed with an icon, "No listings found matching your criteria", and a button to reset filters.

## Technical Notes

- View implementation: `ListingFeedView(TemplateView)` calling `ListingFeedQuery.for_viewer(request.user, ...)`.
- Reuses brand tokens from `brand-tokens.css` and dedicated feed styles in `static/css/listings.css`.
- Offcanvas filter drawer uses standard Bootstrap or lightweight CSS/JS matching Mockup 03.

## Dependencies

### Requires
- `025-listing-feed-query-and-compatibility`

### Enables
- `027-listing-card-and-compatibility-ui`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Malformed query parameters (e.g. `budget_min=abc`) | Sanitized gracefully, falling back to default minimum 500 |
| Multiple areas selected in query string (`?area=Mirpur&area=Dhanmondi`) | Correctly parsed as a list and passed to `ListingFeedQuery` |
| View on mobile screen (< 768px) | Filter drawer occupies full screen width, grid collapses to 1 column |

## Out of Scope

- Detailed listing view (handled in Story `028`).
