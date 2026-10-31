---
id: 010-listing-discovery-and-detail-ui
unit: 002-listing-feed-and-detail-ui
intent: 005-public-listing-feed-and-search
type: simple-construction-bolt
status: planned
stories:
  - 026-feed-view-and-filter-ui
  - 027-listing-card-and-compatibility-ui
  - 028-listing-detail-and-gated-contact-ui
created: '2026-10-31T16:05:00Z'
started: null
completed: null
current_stage: null
stages_completed: []
requires_bolts:
  - 009-listing-feed-query-and-consent
enables_bolts: []
requires_units:
  - 001-listing-feed-query-and-consent
blocks: true
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 1
  testing_scope: 2
---

# Bolt: 010-listing-discovery-and-detail-ui

## Overview
Seeker-facing presentation layer for public listing discovery, responsive filter drawer, listing cards with compatibility indicators, dedicated listing detail page with photo gallery carousel, soft-gated sticky contact panel, and safety reporting signposts matching [Mockup 03](file:///home/bs01496/Documents/LMS/basa-pass/docs/mockups/03-listing-feed.html) (`03-listing-feed.html`) and [Mockup 04](file:///home/bs01496/Documents/LMS/basa-pass/docs/mockups/04-listing-detail.html) (`04-listing-detail.html`).

## Objective
Deliver a fast, responsive, and trustworthy discovery and detail experience for accommodation seekers in Dhaka, featuring interactive filters, rich photography, transparent lifestyle compatibility hints, and soft-gated contact channels per PRD §4.4, §4.5, and Architecture Spine AD-5, AD-12, AD-13.

## Stories Included
- **026-feed-view-and-filter-ui**: Public listing feed view, offcanvas filter drawer, & sorting controls matching Mockup 03 (Must)
- **027-listing-card-and-compatibility-ui**: Reusable listing card with 0–6 compatibility match dots indicator (Must)
- **028-listing-detail-and-gated-contact-ui**: Listing detail page, photo gallery carousel, soft-gated contact card, and audit logging (Must)

## Verification Plan
- View tests asserting anonymous access to `/listings/` and `/listings/<uuid:pk>/`.
- Filter tests asserting filter parameters in URL properly refine the feed results.
- Soft-gated contact tests verifying unverified viewers see locked CTA panel without contact info in DOM, and verified viewers see phone/email with an `AuditEntry` recorded.
- Visual and responsive checks matching Mockups 03 and 04.
