---
unit: 002-listing-feed-and-detail-ui
intent: 005-public-listing-feed-and-search
phase: construction
status: complete
created: '2026-10-31T15:58:00Z'
updated: '2026-11-01T08:26:00Z'
---

# Unit Brief: 002-listing-feed-and-detail-ui

## Purpose

Delivers the public discovery feed view, interactive offcanvas filter drawer, reusable listing cards with 0–6 compatibility badges, dedicated listing detail page with photo gallery carousel, soft-gated sticky contact panel, and safety reporting signposts matching Mockups 03 and 04.

## Scope

### In Scope
- Public `ListingFeedView` CBV at `/listings/` (and alias `/browse/`) with query param binding, sorting, and pagination.
- Offcanvas filter drawer UI with canonical Dhaka area chips, budget slider, kind/unit selectors, and lifestyle preference chips.
- Listing card component (`listing_card.html`) with thumbnail, verified badge, rent, Dhaka area, author avatar, and 0–6 compatibility score visualization.
- Public `ListingDetailView` CBV at `/listings/<uuid:pk>/` with breadcrumbs, photo gallery carousel/thumbnails, host notes (with Bengali script support), and compatibility breakdown.
- Soft-gated contact card: reveals email/phone and triggers audit entry for verified viewers; renders locked panel with CTA for unverified viewers.
- Safety reporting card with escalation mailto link.

### Out of Scope
- Direct database queries or custom ORM filtering (strictly handled via `ListingFeedQuery`).
- PII redaction rules and 6-axis compatibility score calculation (handled in Unit `001`).
- Listing creation and author editing flows (handled in Intent `004`).

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Public feed browsing, active inventory display, and sorting controls | Must |
| FR-2 | Filter drawer UI, chip groups, active filter counter, and reset button | Must |
| FR-4 | Card and detail UI visualization of 0–6 lifestyle compatibility dots | Must |
| FR-5 | Dedicated listing detail surface, photo gallery carousel, and highlights | Must |
| FR-6 | Soft-gated contact card UI, locked CTA panel, and audit logging trigger | Must |
| FR-7 | Safety notice card and escalation link | Should |

---

## Domain Concepts

### Key Surfaces
| Surface | Template Path | Description |
|---------|---------------|-------------|
| Feed View | `templates/listings/feed.html` | Card grid, filter drawer trigger, result bar, sort dropdown, pagination |
| Filter Drawer | `templates/listings/partials/filter_drawer.html` | Offcanvas sidebar with chips, range slider, clear/apply buttons |
| Listing Card | `templates/listings/partials/feed_card.html` | Reusable discovery card with photo, badges, price, area, match dots |
| Detail View | `templates/listings/detail.html` | Breadcrumbs, gallery, host notes, author card, sticky contact/locked panel |

---

## Story Summary

| Metric | Count |
|--------|-------|
| Total Stories | 3 |
| Must Have | 2 |
| Should Have | 1 |
| Could Have | 0 |

### Stories

| Story ID | Title | Priority | Status |
|----------|-------|----------|--------|
| `026-feed-view-and-filter-ui` | Public listing feed view, filter drawer, & sorting controls | Must | Planned |
| `027-listing-card-and-compatibility-ui` | Reusable listing card with 0–6 compatibility match indicator | Must | Planned |
| `028-listing-detail-and-gated-contact-ui` | Listing detail page, photo gallery carousel, & soft-gated contact card | Must | Planned |

---

## Dependencies

### Depends On
| Unit | Reason |
|------|--------|
| `001-listing-feed-query-and-consent` | Provides `ListingFeedQuery` and `ListingProjection` data objects |
| Base templates & tokens | Requires `base.html`, `navbar.html`, `brand-tokens.css`, `listings.css` |

### Depended By
| Unit | Reason |
|------|--------|
| None | Completes Intent 005 |

---

## Success Criteria

### Functional
- [x] Anyone can browse the feed and open listing details without being forced to authenticate.
- [x] Filter drawer accurately updates feed results across area, budget, kind, and lifestyle axes.
- [x] Verified viewers see clickable email (`mailto:`) and phone (`tel:`) with an audit record created.
- [x] Unverified viewers see locked contact panel with clear "Verify your passport" CTA.
- [x] Photo gallery displays full photo and allows thumbnail switching.

### Non-Functional
- [x] Fully responsive on mobile (drawer collapses, single-column card stack).
- [x] Pixel fidelity aligned with Mockup 03 (`03-listing-feed.html`) and Mockup 04 (`04-listing-detail.html`).
- [x] >90% test coverage across view and template rendering tests.

---

## Bolt Suggestions

| Bolt | Type | Stories | Objective |
|------|------|---------|-----------|
| `010-listing-discovery-and-detail-ui` | Simple | 026, 027, 028 | Build feed view, filter drawer, card partials, detail page, gallery, and soft-gated contact |
