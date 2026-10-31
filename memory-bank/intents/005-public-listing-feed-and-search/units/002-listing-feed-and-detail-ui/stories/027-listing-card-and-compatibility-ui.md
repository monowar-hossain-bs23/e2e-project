---
id: 027-listing-card-and-compatibility-ui
unit: 002-listing-feed-and-detail-ui
intent: 005-public-listing-feed-and-search
status: ready
priority: must
created: '2026-10-31T16:00:00Z'
assigned_bolt: 010-listing-discovery-and-detail-ui
implemented: false
---

# Story: 027-listing-card-and-compatibility-ui

## User Story

**As a** seeker browsing the feed
**I want** each listing card to clearly display the photo, rent, area, lister verified status, and my lifestyle match score
**So that** I can assess flat suitability at a glance before clicking for full details.

## Acceptance Criteria

- [ ] **Given** a listing in the feed, **When** its card renders, **Then** it features the primary photo (16:10 aspect ratio), kind tag (`SEAT` or `ROOM`), green verified shield badge (`Verified`), rent formatted in BDT (`৳X,XXX`), rent unit (`/ seat` or `/ room`), Dhaka neighborhood, author avatar with tenure, and a "View listing" link matching [Mockup 03](file:///home/bs01496/Documents/LMS/basa-pass/docs/mockups/03-listing-feed.html#L314-L470).
- [ ] **Given** an authenticated seeker with a verified passport, **When** viewing cards, **Then** the compatibility row renders 6 dots with count label *"matches X of 6 preferences"*:
  - If $X \ge 4$: green filled dots (`--bp-success`) and success green text (`--bp-success-fg`).
  - If $X < 4$: grey dots and muted text (`--bp-muted`).
- [ ] **Given** an anonymous visitor or unverified user, **When** viewing cards, **Then** the compatibility row displays empty/neutral dots with the text *"Verify to see lifestyle fit"*.
- [ ] **Given** a card in hover state, **When** user hovers over it, **Then** a subtle vertical lift (`translateY(-2px)`) and teal elevation shadow appear.

## Technical Notes

- Implements Architecture Spine AD-5 (reusable component partial: `templates/listings/partials/feed_card.html`).
- Bengali script in body excerpt uses `lang="bn"` styling.
- Compatible with desktop 3-column grid and mobile single-column view.

## Dependencies

### Requires
- `025-listing-feed-query-and-compatibility`
- `026-feed-view-and-filter-ui`

### Enables
- `028-listing-detail-and-gated-contact-ui`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Listing has no photos uploaded | Displays brand pattern placeholder with kind label |
| Lister display name is long (> 20 chars) | Name truncates cleanly with ellipsis without breaking card layout |
| Long body excerpt | Clamped to 2 lines via `-webkit-line-clamp: 2` |

## Out of Scope

- Contact disclosure (handled on detail page in Story `028`).
