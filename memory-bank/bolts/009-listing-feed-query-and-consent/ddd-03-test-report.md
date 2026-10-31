---
unit: 001-listing-feed-query-and-consent
bolt: 009-listing-feed-query-and-consent
stage: test
status: complete
updated: '2026-11-01T01:15:00Z'
---

# Test Report - Listing Feed Query & Consent Projection

## Test Summary

| Category | Passed | Failed | Skipped | Status |
|----------|--------|--------|---------|--------|
| Unit (ConsentService & Projections) | 5 | 0 | 0 | ✅ Pass |
| Unit (CompatibilityEngine 6-Axis) | 9 | 0 | 0 | ✅ Pass |
| Integration (ListingFeedQuery & Filtering) | 13 | 0 | 0 | ✅ Pass |
| Regression (Scaffolding, Accounts, Passports, Verification, Listings) | 225 | 0 | 0 | ✅ Pass |
| **Total Test Suite** | **252** | **0** | **0** | **100% Pass** |

---

## Acceptance Criteria Validation

| Story | Criteria | Status |
|-------|----------|--------|
| **024-listing-consent-service-and-projection** | `ListingProjection` and `PhotoProjection` immutable dataclasses with viewer-scoped contact and lifestyle fields | ✅ |
| **024-listing-consent-service-and-projection** | `ConsentService.render_listing` soft-gates phone and email (`None`) for anonymous visitors | ✅ |
| **024-listing-consent-service-and-projection** | `ConsentService.render_listing` soft-gates phone and email (`None`) for unverified registered users | ✅ |
| **024-listing-consent-service-and-projection** | Verified seekers receive unlocked phone and email contact channels | ✅ |
| **024-listing-consent-service-and-projection** | Listing author viewing their own listing always sees their own unredacted contact channels | ✅ |
| **024-listing-consent-service-and-projection** | `ConsentService.compute_author_tenure` formats days, months, and years of verification accurately | ✅ |
| **024-listing-consent-service-and-projection** | `ConsentService.extract_author_lifestyle` extracts human-readable summary and tag chips | ✅ |
| **025-listing-feed-query-and-compatibility** | `ListingFeedQuery.for_viewer` enforces active inventory invariants (excludes withdrawn, archived, or >60d stale listings) | ✅ |
| **025-listing-feed-query-and-compatibility** | Zero N+1 queries guaranteed on batch feeds using `select_related` and `prefetch_related` (constant 4 SQL queries) | ✅ |
| **025-listing-feed-query-and-compatibility** | Additive filtering on single/multiple areas, budget range (`min`/`max`), kind (`SEAT`/`ROOM`), rent unit | ✅ |
| **025-listing-feed-query-and-compatibility** | Lifestyle filtering on gender, smoking, sleep schedule, and target occupations | ✅ |
| **025-listing-feed-query-and-compatibility** | Sorting options supported: `newest` (default), `rent_asc`, `rent_desc` | ✅ |
| **025-listing-feed-query-and-compatibility** | Deterministic pagination with 12 items/page default and standard Django `Paginator` API | ✅ |
| **025-listing-feed-query-and-compatibility** | `CompatibilityEngine` computes objective transparent integer score $X \in [0, 6]$ across all 6 lifestyle axes | ✅ |
| **025-listing-feed-query-and-compatibility** | `ListingFeedQuery.get_detail_for_viewer` logs append-only `AuditEntry` (`contact_viewed`) on contact reveal | ✅ |
| **025-listing-feed-query-and-compatibility** | Listing author viewing own detail page does not trigger external contact disclosure audit | ✅ |

---

## Detailed Test Suite Results

### 1. ConsentService & Projection Unit Tests (`tests/test_passports/test_consent_service.py`)
- `test_anonymous_viewer_redacts_contact_info`: Confirms anonymous visitors receive `None` for email and phone, `is_contact_locked=True`, and gated lifestyle summary.
- `test_unverified_viewer_redacts_contact_info`: Confirms logged-in unverified users receive locked contact information.
- `test_verified_viewer_reveals_contact_info`: Confirms verified seekers receive full phone, email, author display name, and lifestyle chips.
- `test_author_always_views_own_contact_details`: Confirms authors can view their own contact information regardless of viewer flags.
- `test_author_tenure_display_calculation`: Verifies tenure string formatting across day, month, and year intervals from reviewed verification dates.

### 2. CompatibilityEngine Unit Tests (`tests/test_listings/test_compatibility.py`)
- `test_evaluate_gender_axis`: Strict match on identical gender or listing `any`.
- `test_evaluate_smoking_axis`: Verified non-smoker / smoker matching with listing `any`.
- `test_evaluate_sleep_schedule_axis`: Night owl vs early bird matching with listing `flexible`.
- `test_evaluate_occupation_axis`: Seeker occupation membership in listing occupation array or listing `any`.
- `test_evaluate_area_axis`: Listing area membership in seeker preferred area list.
- `test_evaluate_budget_axis`: Strict check that listing rent does not exceed seeker max budget.
- `test_evaluate_full_perfect_match`: 6/6 perfect score when all axes align.
- `test_evaluate_none_profile_returns_zero`: Safely returns 0 score and empty match dict when seeker profile is absent.

### 3. ListingFeedQuery Integration Tests (`tests/test_listings/test_feed_query.py`)
- `test_feed_excludes_withdrawn_listings`: Verifies withdrawn accommodation listings are filtered out.
- `test_feed_excludes_archived_listings`: Verifies explicitly archived listings are excluded.
- `test_feed_excludes_stale_listings_over_60_days`: Verifies listings older than 60 days are auto-excluded.
- `test_feed_filter_by_area`: Verifies area filtering by canonical Dhaka sub-area string.
- `test_feed_filter_by_budget_range`: Verifies filtering by min and max rent thresholds.
- `test_feed_filter_by_kind_and_rent_unit`: Verifies filtering by room/seat and corresponding rent unit.
- `test_feed_filter_by_lifestyle_preferences`: Verifies additive lifestyle filtering on gender, smoking, sleep, and occupations.
- `test_feed_sorting_options`: Verifies newest first, rent ascending, and rent descending ordering.
- `test_feed_compatibility_hint_attached_for_verified_seeker`: Verifies compatibility scores dynamically attached to projections.
- `test_feed_pagination`: Verifies page slicing and total count calculation.
- `test_feed_zero_n_plus_one_queries`: Executes batch feed read of 10 listings with primary photos under strict `assertNumQueries(4)` (1 count, 1 select_related, 2 prefetch).
- `test_detail_query_verified_viewer_emits_audit`: Verifies single listing detail fetch by verified viewer records `contact_viewed` in `AuditEntry`.
- `test_detail_query_author_does_not_emit_external_audit`: Verifies author accessing own listing detail does not write an external viewer audit record.
