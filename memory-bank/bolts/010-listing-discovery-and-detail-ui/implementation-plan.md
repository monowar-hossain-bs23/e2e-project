---
unit: 002-listing-feed-and-detail-ui
bolt: 010-listing-discovery-and-detail-ui
stage: plan
status: ready-for-review
updated: '2026-11-01T01:25:00Z'
---

# Implementation Plan - Listing Discovery & Detail UI

## 1. Objectives & Scope

Deliver the seeker-facing discovery presentation layer and public detail view for accommodation listings in Dhaka. Implements Stories **026**, **027**, and **028**, strictly adhering to Architecture Spine AD-3, AD-5, AD-8, AD-12, AD-13, and PRD §4.4, §4.5, matching [Mockup 03](file:///home/bs01496/Documents/LMS/basa-pass/docs/mockups/03-listing-feed.html) (`03-listing-feed.html`) and [Mockup 04](file:///home/bs01496/Documents/LMS/basa-pass/docs/mockups/04-listing-detail.html) (`04-listing-detail.html`).

---

## 2. Deliverables & Technical Architecture

### A. URL Routing & Public Allow-List
- **`config/urls_public.py`**:
  - Add `"listing_feed"` and `"listing_detail"` to `PUBLIC_URL_NAMES` (AD-8).
- **`apps/listings/urls.py`**:
  - `GET /listings/` -> `ListingFeedView` (name: `"listing_feed"`)
  - `GET /listings/<uuid:pk>/` -> `ListingDetailView` (name: `"listing_detail"`)

### B. Class-Based Views (`apps/listings/views.py`)
- **`ListingFeedView(TemplateView)`**:
  - Read-only public template view.
  - Parses GET query parameters:
    - `areas` (list of sub-areas or single string)
    - `budget_min`, `budget_max` (integers, with error fallbacks)
    - `kind` (`seat` or `room`)
    - `rent_unit` (`per_seat` or `per_room`)
    - `gender`, `smoking`, `sleep`, `occupations` (lifestyle filters)
    - `sort` (`newest`, `rent_asc`, `rent_desc`)
    - `page` (integer, default: 1)
  - Invokes `ListingFeedQuery.for_viewer(request.user, ...)`.
  - Calculates `active_filter_count` to display on the filter trigger button badge pill.
  - Supplies context:
    - `projections`: list of `ListingProjection` objects
    - `page_obj`: paginator page slice
    - `total_count`: total matching active listings
    - `active_filter_count`: integer badge count
    - `current_sort`: current sort key
    - `dhaka_areas`: canonical 13 Dhaka sub-areas from `DHAKA_SUB_AREAS`
    - Form choices for kinds, genders, smoking, sleep schedules, occupations.
- **`ListingDetailView(DetailView)` / `TemplateView`**:
  - Fetches projection via `ListingFeedQuery.get_detail_for_viewer(viewer=request.user, listing_id=pk)`.
  - If returned `proj` is `None`, raises `Http404("Listing not found or no longer active.")`.
  - Context provides `listing: ListingProjection`, `is_author: bool`.

### C. Templates & Component Partials
- **`templates/listings/feed.html`**:
  - Top navigation bar integration with active "Browse" link.
  - Page header: *"Find verified accommodation in Dhaka"*.
  - Result bar: Active count (`Showing X active seats & rooms`), filter trigger button with active count badge pill, and sort dropdown.
  - Offcanvas filter drawer (sidebar):
    - Dhaka area chip group (13 canonical sub-areas with multi-select).
    - Accommodation kind chips (`Seat`, `Room`).
    - Budget range slider / numerical inputs (৳500 – ৳50,000).
    - Lifestyle filters: Gender chips (`Any`, `Male`, `Female`), Smoking chips (`Any`, `Non-smoker`, `Smoker`), Sleep schedule chips (`Flexible`, `Early bird`, `Night owl`), Occupation chips.
    - Drawer footer: "Clear all" reset button and "Apply filters" button.
  - 3-column responsive card grid (`row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4`).
  - Empty state with reset filters button when zero listings match.
  - Pagination bar with Previous, page numbers, and Next controls.
- **`templates/listings/partials/feed_card.html`**:
  - Reusable card partial per AD-5.
  - 16:10 photo ratio with image fallback pattern.
  - Tags: Kind badge (`SEAT` / `ROOM`) and green verified shield badge.
  - Pricing & location: `৳X,XXX/seat` or `/room`, Dhaka area.
  - Author info: Avatar, display handle, verification tenure.
  - Compatibility row:
    - For verified seeker: 6 dots with match label (*"matches X of 6 preferences"*).
    - For unverified / anonymous: Neutral empty dots with *"Verify to see lifestyle fit"*.
  - Body excerpt clamped to 2 lines with Bengali text support.
  - Card hover lift and teal shadow elevation.
- **`templates/listings/detail.html`**:
  - Breadcrumbs: `Browse > [Area] > [Kind]`.
  - Photo gallery carousel: High-resolution primary viewport with thumbnail strip (1 to 7 photos) and click-to-view interaction.
  - Headline block: Kind badge, formatted rent, Dhaka area, post date.
  - Full host description supporting Bengali text (`lang="bn"`).
  - Author card: Avatar, display name, verified tenure, verified shield badge, lifestyle profile chips.
  - Right-column sticky contact panel:
    - **Verified Seeker**: Direct clickable email (`mailto:`) and phone (`tel:`), off-platform notice (*"Basha Pass doesn't run in-app messaging"*), Save and Share buttons.
    - **Unverified / Anonymous**: Locked card with shield-lock icon, *"Verify to see contact info"*, *"Start verification"* CTA button routing to `/passports/create/` (or login). Zero email/phone strings in DOM.
  - 6-axis compatibility card:
    - 0–6 dots score with breakdown checklist (green checks and muted crosses for gender, smoking, sleep, occupation, area, budget).
  - Lister preferences checklist table.
  - Safety report card linking to `mailto:support@bashapass.com?subject=Report%20Listing%20[ID]`.

### D. Styles & Client-Side Scripts
- **`static/css/listings.css`**:
  - Styles extracted and refined from Mockups 03 and 04.
  - `.bp-listing-card`, `.bp-filter-drawer`, `.bp-sort`, `.bp-compat`, `.bp-contact`, `.bp-locked`, `.bp-gallery`.
- **`static/js/listing-feed.js`**:
  - Offcanvas filter drawer open, close, and clear-all events.
  - Budget slider live value display update.
- **`static/js/listing-detail.js`**:
  - Photo gallery thumbnail click switcher updating main image source and active thumbnail border.

---

## 3. Acceptance Criteria & Validation Matrix

| Criterion | Verification Method |
|-----------|---------------------|
| Public feed accessible to unauthenticated visitors | HTTP GET `/listings/` returns 200 without login redirect |
| Filter drawer submits GET params and refines queryset | GET `/listings/?area=Mirpur&budget_max=5000` asserts filtered results |
| Zero results shows friendly empty state | GET with non-matching filters displays empty state card |
| Verified seeker cards display 0–6 match score dots | Assert card HTML contains `.bp-dots` with match count |
| Unverified viewer cards display "Verify to see lifestyle fit" | Assert anonymous view contains locked tooltip text |
| Single listing detail viewable publicly | HTTP GET `/listings/<id>/` returns 200 |
| Verified viewer detail view unlocks contact and logs `AuditEntry` | Assert response contains email/phone and DB contains `action='contact_viewed'` |
| Unverified / anonymous detail view redacts contact info completely | Assert response HTML contains 0 instances of author email/phone |
| Withdrawn or archived listing returns 404 for non-owners | Non-author GET request returns 404 |

---

## 4. Dependencies
- **Bolt 009** (`009-listing-feed-query-and-consent`): Complete (provides `ListingFeedQuery`, `ConsentService`, `CompatibilityEngine`).
- **AuditService**: Available for contact disclosure audit logging.
