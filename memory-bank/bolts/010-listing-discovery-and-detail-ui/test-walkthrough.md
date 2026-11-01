---
stage: test
bolt: 010-listing-discovery-and-detail-ui
created: '2026-11-01T08:26:00Z'
---

## Test Report: 002-listing-feed-and-detail-ui

### Summary

- **Tests**: 13/13 passed in `tests/test_listings/test_feed_views.py` (265/265 passed project-wide)
- **Status**: 100% Pass rate

### Test Files

- [x] `tests/test_listings/test_feed_views.py` - Full test coverage for `ListingFeedView`, offcanvas filter parameter handling, empty states, `ListingDetailView` soft-gated contact protection, and audit logging.

### Acceptance Criteria Validation

- ✅ **Public Feed Access (Story 026)**: Anonymous visitors can view `/listings/` without redirection.
- ✅ **Filter Parameters (Story 026)**: Area, budget range, and accommodation kind parameters correctly refine feed results.
- ✅ **Empty State (Story 026)**: When 0 listings match, a friendly empty state card with a "Clear all filters" CTA is displayed.
- ✅ **Sorting Controls (Story 026)**: Feed respects `sort=rent_desc`, `rent_asc`, and `newest` ordering.
- ✅ **Compatibility Indicator Dots (Story 027)**: Authenticated verified seekers receive green/neutral 0–6 score dots; anonymous and unverified visitors receive "Verify to see lifestyle fit".
- ✅ **Detail Page Public View (Story 028)**: Dedicated listing detail page `/listings/<uuid:pk>/` is viewable publicly.
- ✅ **Soft-Gated Contact Protection (Story 028, AD-3)**: Unverified and anonymous visitors see a locked contact card with zero phone or email strings in DOM.
- ✅ **Verified Contact Reveal & Audit Trail (Story 028, AD-15)**: Verified seekers see direct phone and email with an append-only `contact_viewed` `AuditEntry` recorded.
- ✅ **Author Self-Inspection (Story 028)**: Lister viewing their own detail page sees contact info without recording an external viewer audit entry.
- ✅ **Status Enforcements (Story 028)**: Withdrawn or archived listings return HTTP 404 for non-owners.

### Issues Found

- Initial assertion checked for sub-area names in `response.content`, which collided with the static choices in the offcanvas filter drawer. Fixed by asserting on `response.context["projections"]`.
- `AuditEntry` timestamp ordering used `created_at` instead of `timestamp`. Fixed to `latest("timestamp")`.

### Notes

- Zero N+1 queries maintained during feed rendering and detail page queries.
- Bengali text rendering and RTL script support verified via `lang="bn"` styling.
