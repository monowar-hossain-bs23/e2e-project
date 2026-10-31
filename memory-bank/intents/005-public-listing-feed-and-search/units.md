---
intent: 005-public-listing-feed-and-search
phase: inception
status: in-progress
updated: '2026-10-31T15:56:00Z'
---

# 005-public-listing-feed-and-search - Unit Decomposition

## Units Overview

This intent decomposes into 2 distinct units of work, cleanly separating the high-performance read-model query engine, PII projection, and compatibility scoring from the user-facing discovery feed, filter drawer, and detailed listing presentation surfaces:

### Unit 1: `001-listing-feed-query-and-consent`

**Description**: Backend read-model query abstraction, viewer consent projection, 6-axis lifestyle compatibility scoring, and contact disclosure audit logging. Enforces PRD FR-11/FR-12, ERD §4, and Architecture Spine AD-3, AD-12, AD-15.

**Stories**:
- `024-listing-consent-service-and-projection`: `ConsentService` (`apps/passports/services/consent_service.py` / `apps/listings/services/consent.py`), projection data structures, and verified vs unverified PII redaction rules (AD-3).
- `025-listing-feed-query-and-compatibility`: `ListingFeedQuery` read model (`apps/listings/services/feed_query.py`), multi-axis filtering, sorting (newest, rent asc, rent desc), pagination, 60-day auto-filtering, and 6-axis lifestyle compatibility scoring (AD-12).

**Deliverables**:
- `apps/passports/services/consent_service.py` (or `apps/listings/services/consent.py`)
- `apps/listings/services/feed_query.py` (`ListingFeedQuery`, `ListingProjection`)
- Comprehensive unit tests covering all filter dimensions, projection redactions, and 6-axis match scoring (`tests/test_listings/test_feed_query.py`, `tests/test_passports/test_consent.py`).

**Dependencies**:
- Depends on: `apps.listings` (Listing models), `apps.passports` (Passport & LifestyleProfile models), `apps.audit` (`AuditService`).
- Depended by: `002-listing-feed-and-detail-ui`.

**Estimated Complexity**: L (Large — complex multi-axis query builder, 6-axis matching, zero N+1 enforcement, PII protection).

---

### Unit 2: `002-listing-feed-and-detail-ui`

**Description**: Seeker-facing presentation layer for public listing discovery, responsive filter drawer, listing cards with compatibility indicators, dedicated listing detail page with photo gallery, soft-gated contact card, and audit logging. Realizes Mockup 03 (`03-listing-feed.html`) and Mockup 04 (`04-listing-detail.html`).

**Stories**:
- `026-feed-view-and-filter-ui`: `ListingFeedView` CBV at `/listings/` with search query parameter handling, filter drawer offcanvas UI, chip groups, active count badge, sorting menu, and pagination.
- `027-listing-card-and-compatibility-ui`: Componentized `listing_card.html` rendering primary photo, kind badge, verified badge, rent, Dhaka area, author avatar, and 0–6 compatibility dots with success/muted states.
- `028-listing-detail-and-gated-contact-ui`: `ListingDetailView` CBV at `/listings/<uuid:pk>/`, breadcrumbs, photo gallery carousel, accommodation highlights, sticky soft-gated contact panel with audit logging (`contact_viewed`), locked CTA panel for unverified viewers, and safety reporting card.

**Deliverables**:
- `apps/listings/views.py` (`ListingFeedView`, `ListingDetailView`)
- `templates/listings/feed.html`, `templates/listings/detail.html`
- `templates/listings/partials/filter_drawer.html`, `templates/listings/partials/contact_panel.html`
- `static/css/feed.css` / `static/css/detail.css` (or additions to `listings.css` matching Mockups 03 and 04)
- `static/js/feed-filter.js`, `static/js/detail-gallery.js`
- Automated view & integration tests (`tests/test_listings/test_feed_views.py`, `tests/test_listings/test_detail_views.py`).

**Dependencies**:
- Depends on: `001-listing-feed-query-and-consent`, `apps/listings/urls.py`, `brand-tokens.css`.
- Depended by: None (end-user discovery feature complete).

**Estimated Complexity**: M (Medium — responsive UI mockups, gallery carousel, soft-gating logic, audit emission).
