---
unit: 001-listing-feed-query-and-consent
intent: 005-public-listing-feed-and-search
phase: inception
status: ready
created: '2026-10-31T15:58:00Z'
updated: '2026-10-31T15:58:00Z'
---

# Unit Brief: 001-listing-feed-query-and-consent

## Purpose

Provides the unified, high-performance read-model query engine ([`ListingFeedQuery`](file:///home/bs01496/Documents/LMS/basa-pass/docs/ARCHITECTURE-SPINE.md#L173-L181)), projection transformation service ([`ConsentService`](file:///home/bs01496/Documents/LMS/basa-pass/docs/ARCHITECTURE-SPINE.md#L60-L75)), and lifestyle compatibility matching engine (0–6 score) for all accommodation discovery surfaces. Enforces strict PII exclusion for unverified viewers, eliminates N+1 queries, and manages contact disclosure audit logging.

## Scope

### In Scope
- `ConsentService.render(viewer, item) -> Projection` implementing viewer-scoped PII shielding rules (AD-3).
- `ListingFeedQuery.for_viewer()` sole read-model query method with multi-axis filtering, sorting, pagination, and eager query loading (AD-12).
- Server-side 6-axis lifestyle compatibility match engine producing integer scores $X \in [0, 6]$ based on gender, smoking, sleep, occupation, area, and budget.
- Automatic filtering of stale (>60d), withdrawn, and archived listings from public discovery.
- Integration with `AuditService` for contact revelation tracking (`contact_viewed`).

### Out of Scope
- HTML template rendering and layout styling (handled in Unit `002`).
- Offcanvas filter drawer UI and carousel JavaScript controls (handled in Unit `002`).
- Listing creation, mutation, and photo file storage (handled in Intent `004`).

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Public feed active inventory invariants and sorting support | Must |
| FR-2 | Multi-axis filter query logic (area, budget, kind, lifestyle) | Must |
| FR-3 | `ListingFeedQuery` read-model abstraction & batch optimization | Must |
| FR-4 | Lifestyle compatibility match heuristic (0–6 integer score) | Must |
| FR-6 | Conditional PII projection and audit logging on contact reveal | Must |

---

## Domain Concepts

### Key Entities
| Entity | Description | Attributes |
|--------|-------------|------------|
| `ListingProjection` | Immutable read projection of a listing for a specific viewer | `id`, `kind`, `rent_bdt`, `rent_unit`, `area`, `body`, `photos`, `author_display_name`, `author_tenure`, `is_author_verified`, `email`, `phone`, `compatibility_hint` |
| `ViewerProtocol` | Abstract protocol identifying the viewer and their verification status | `user`, `is_authenticated`, `is_verified`, `passport` |

### Key Operations
| Operation | Description | Inputs | Outputs |
|-----------|-------------|--------|---------|
| `ListingFeedQuery.for_viewer` | Retrieves filtered, paginated listing projections | `viewer`, `area`, `budget_min`, `budget_max`, `kind`, `rent_unit`, `gender`, `smoking`, `sleep`, `occupation`, `sort`, `page` | `PaginatedProjections` |
| `ConsentService.render` | Transforms raw listing/passport model into viewer-safe projection | `viewer`, `listing` | `ListingProjection` |
| `CompatibilityEngine.compute` | Computes intersection of seeker lifestyle profile against listing preferences | `seeker_profile`, `listing` | `int` (0 to 6) |

---

## Story Summary

| Metric | Count |
|--------|-------|
| Total Stories | 2 |
| Must Have | 2 |
| Should Have | 0 |
| Could Have | 0 |

### Stories

| Story ID | Title | Priority | Status |
|----------|-------|----------|--------|
| `024-listing-consent-service-and-projection` | `ConsentService` & viewer-scoped PII projection | Must | Planned |
| `025-listing-feed-query-and-compatibility` | `ListingFeedQuery` read model & 6-axis compatibility score | Must | Planned |

---

## Dependencies

### Depends On
| Unit | Reason |
|------|--------|
| `001-listing-domain-service` | Access to `Listing` and `ListingPhoto` models and status checks |
| `001-passport-and-verification-domain` | Access to `Passport` and `LifestyleProfile` models |
| `apps.audit` | `AuditService.append()` for contact disclosure logging |

### Depended By
| Unit | Reason |
|------|--------|
| `002-listing-feed-and-detail-ui` | Consumes `ListingFeedQuery` and `ListingProjection` for rendering |

---

## Technical Context

### Suggested Technology
- Python dataclasses or Pydantic models for immutable `ListingProjection`.
- Django ORM composite `Q` objects for multi-axis additive AND / OR filtering.
- Django `Paginator` for standard pagination slice.

---

## Success Criteria

### Functional
- [ ] Unverified and anonymous viewers receive `email=None` and `phone=None` in projections.
- [ ] Verified viewers receive full contact details.
- [ ] 6-axis compatibility heuristic accurately evaluates the 6 lifestyle dimensions returning 0 to 6.
- [ ] Listings >60 days old, archived, or withdrawn are excluded from public feed.

### Non-Functional
- [ ] Feed query execution executes in < 150ms p95 on 10,000 listings.
- [ ] Eager loading ensures constant query count regardless of page size.
- [ ] 100% test coverage on `ConsentService` and `ListingFeedQuery`.

---

## Bolt Suggestions

| Bolt | Type | Stories | Objective |
|------|------|---------|-----------|
| `009-listing-feed-query-and-consent` | DDD | 024, 025 | Implement `ConsentService`, `ListingFeedQuery`, compatibility scoring, and contact audit logging |
