---
id: 025-listing-feed-query-and-compatibility
unit: 001-listing-feed-query-and-consent
intent: 005-public-listing-feed-and-search
status: ready
priority: must
created: '2026-10-31T16:00:00Z'
assigned_bolt: 009-listing-feed-query-and-consent
implemented: false
---

# Story: 025-listing-feed-query-and-compatibility

## User Story

**As a** prospective seeker browsing listings
**I want** a unified query engine that filters active listings across Dhaka areas, rent, and lifestyle preferences while computing an objective 0–6 lifestyle compatibility score
**So that** I quickly find relevant flats that match my budget, location, and lifestyle.

## Acceptance Criteria

- [ ] **Given** active and inactive listings in the database, **When** `ListingFeedQuery.for_viewer(viewer, ...)` is called, **Then** all listings with `withdrawn_at IS NOT NULL`, `archived_at IS NOT NULL`, or `created_at < now() - 60 days` are excluded from the result set.
- [ ] **Given** search filter parameters (`areas`, `budget_min`, `budget_max`, `kind`, `rent_unit`, `gender`, `smoking`, `sleep`, `occupation`), **When** `ListingFeedQuery.for_viewer` executes, **Then** filters are combined with an additive AND across categories and OR within multi-select categories (`area__in`, `pref_occupation__contains` or matching logic).
- [ ] **Given** a sort parameter (`sort='newest' | 'rent_asc' | 'rent_desc'`), **When** the query executes, **Then** the results are ordered by `-created_at`, `rent_bdt`, or `-rent_bdt` accordingly.
- [ ] **Given** a viewer with a verified passport and complete lifestyle profile, **When** listings are returned, **Then** each item carries a server-side `compatibility_hint: int` computed as the count (0 to 6) of matching axes (gender, smoking, sleep, occupation, area, budget).
- [ ] **Given** an anonymous viewer or unverified seeker, **When** listings are returned, **Then** `compatibility_hint` is `None` (templates render "Verify to see lifestyle fit").
- [ ] **Given** a feed query request for page $P$ with page size 12, **When** the query executes, **Then** `select_related('author__user')` and `prefetch_related('photos')` ensure a constant, fixed number of SQL queries regardless of item count.

## Technical Notes

- Implements Architecture Spine AD-12 (`ListingFeedQuery` is the sole source of any list of Listings).
- Lifestyle compatibility algorithm:
  1. Gender: `pref_gender == 'any'` or `== profile.gender`
  2. Smoking: `pref_smoking == 'any'` or `== profile.smoking`
  3. Sleep: `pref_sleep == 'flexible'` or `== profile.sleep_schedule`
  4. Occupation: `'any' in pref_occupation` or `profile.occupation in pref_occupation`
  5. Area: `listing.area in profile.preferred_areas`
  6. Rent: `listing.rent_bdt <= profile.budget_bdt`
- Returns paginated `ListingProjection` objects.

## Dependencies

### Requires
- `024-listing-consent-service-and-projection`
- `018-listing-service-and-active-cap`

### Enables
- `026-feed-view-and-filter-ui`
- `027-listing-card-and-compatibility-ui`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Seeker profile has empty preferred areas | Area axis evaluates as non-matching (0 for that axis) |
| Listing has no photos | Default placeholder image fallback attached in projection |
| Requested page number exceeds total pages | Returns empty page or last page per standard Django Paginator |

## Out of Scope

- HTML template rendering and layout styling (handled in Unit `002`).
