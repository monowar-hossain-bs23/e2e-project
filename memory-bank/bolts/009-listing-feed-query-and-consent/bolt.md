---
id: 009-listing-feed-query-and-consent
unit: 001-listing-feed-query-and-consent
intent: 005-public-listing-feed-and-search
type: ddd-construction-bolt
status: complete
stories:
  - 024-listing-consent-service-and-projection
  - 025-listing-feed-query-and-compatibility
created: '2026-10-31T16:05:00Z'
started: '2026-10-31T17:00:00Z'
completed: '2026-11-01T01:15:00Z'
current_stage: complete
stages_completed:
  - model
  - design
  - test
  - implement
requires_bolts:
  - 007-listing-domain-service
  - 008-listing-management-ui
enables_bolts:
  - 010-listing-discovery-and-detail-ui
requires_units:
  - 001-listing-domain-service
blocks: false
complexity:
  avg_complexity: 3
  avg_uncertainty: 2
  max_dependencies: 2
  testing_scope: 2
---

# Bolt: 009-listing-feed-query-and-consent

## Overview
High-performance read-model query engine ([`ListingFeedQuery`](file:///home/bs01496/Documents/LMS/basa-pass/docs/ARCHITECTURE-SPINE.md#L173-L181)), projection transformation service ([`ConsentService`](file:///home/bs01496/Documents/LMS/basa-pass/docs/ARCHITECTURE-SPINE.md#L60-L75)), and lifestyle compatibility matching engine (0–6 score) for all accommodation discovery surfaces. Enforces strict PII exclusion for unverified viewers, eliminates N+1 queries through eager query loading, excludes stale (>60d), withdrawn, and archived posts, and integrates with `AuditService` for contact disclosure logging.

## Objective
Establish the robust read layer and privacy projection boundary for Basha Pass accommodation discovery, guaranteeing privacy for listers, transparent lifestyle matching for seekers, and zero N+1 database bottlenecks per PRD §4.4, §4.5, and Architecture Spine AD-3, AD-12, AD-15.

## Stories Included
- **024-listing-consent-service-and-projection**: `ConsentService` & viewer-scoped PII projection shielding lister contact info from unverified viewers (Must)
- **025-listing-feed-query-and-compatibility**: `ListingFeedQuery` read model, multi-axis filtering, sorting (newest, rent asc, rent desc), and 6-axis compatibility score calculation (Must)

## Verification Plan
- Unit tests for `ConsentService` verifying strict redaction of `email` and `phone` for anonymous and unverified viewers.
- Integration tests for `ListingFeedQuery` verifying multi-axis filtering (area, budget range, kind, lifestyle), sorting options, and pagination.
- Query count tests asserting zero N+1 queries on batch reads.
- Compatibility engine tests verifying exact integer scores $X \in [0, 6]$ across all combinations of lifestyle preferences.
