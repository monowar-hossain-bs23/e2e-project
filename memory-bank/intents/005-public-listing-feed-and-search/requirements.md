---
intent: 005-public-listing-feed-and-search
phase: inception
status: draft
created: '2026-10-31T13:15:00Z'
updated: '2026-10-31T15:52:00Z'
---

# Requirements: Public Listing Feed and Search Discovery

## Intent Overview

Enables flat and mess seekers to discover, filter, and inspect accommodation listings (seats in messes or private rooms) across Dhaka. Provides a high-performance public feed with multi-axis filtering (area, budget range, accommodation kind, lifestyle preferences), a dedicated listing detail view with photo gallery, a server-side 6-axis lifestyle compatibility hint (0–6 score), and a soft-gated contact panel where lister contact details (email and phone) are revealed strictly to verified tenants and recorded via append-only audit logs.

## Business Goals

| Goal | Success Metric | Priority |
|------|----------------|----------|
| G-1: Frictionless Discovery | Anyone can search and view listings across Dhaka without an upfront login wall. | Must |
| G-2: Two-Sided Trust Shield | 100% of lister contact details (phone, email) are shielded from unverified viewers. | Must |
| G-3: Objective Lifestyle Compatibility | Seekers see a transparent 0–6 lifestyle match score without black-box algorithmic ranking. | Must |
| G-4: High-Performance Feed | Feed queries execute in < 150ms p95 with zero N+1 database queries. | Must |
| G-5: Auditability | 100% of contact reveal events are logged to the immutable `AuditEntry` stream. | Must |

---

## Functional Requirements

### FR-1: Public Feed Browsing & Active Inventory Invariants
- **Description**: A public listing feed at `/listings/` (or `/browse/`) accessible to both anonymous visitors and authenticated users. The feed displays active accommodation listings in Dhaka.
- **Acceptance Criteria**:
  - Anonymous visitors, unverified users, and verified tenants can all access the feed without authentication redirects.
  - Displays active listings only: excludes withdrawn listings (`withdrawn_at IS NOT NULL`), archived listings (`archived_at IS NOT NULL`), and stale listings older than 60 days (`created_at < now() - 60 days`).
  - Default sort order is newest first (`-created_at`).
  - Supports user-selectable sorting:
    - Newest first (`sort=newest` or default)
    - Rent: Low to High (`sort=rent_asc`)
    - Rent: High to Low (`sort=rent_desc`)
  - Paginated at 12 listings per page with previous/next and numeric page controls.
  - When no listings match the query, renders an informative empty state with a "Clear all filters" affordance.
- **Priority**: Must
- **Related Stories**: `024-listing-feed-query`, `026-feed-view-and-card-rendering`

### FR-2: Multi-Axis Discovery Search & Filtering
- **Description**: Seekers can filter the listing feed across location, financial, accommodation, and lifestyle dimensions. Filtering logic applies an additive AND across distinct filter categories, and an OR within multi-select categories.
- **Acceptance Criteria**:
  - **Area**: Multi-select filter across the 13 canonical Dhaka sub-areas (`area__in=selected_areas`).
  - **Budget Range**: Minimum and maximum rent slider/inputs bounded between ৳500 and ৳50,000 BDT (`rent_bdt__gte` and `rent_bdt__lte`).
  - **Accommodation Kind**: Single-select choice of `seat`, `room`, or any.
  - **Rent Unit**: Filter by `per_seat` or `per_room`.
  - **Roommate Lifestyle Preferences**:
    - Preferred Gender: `male`, `female`, or `any`.
    - Smoking: `yes`, `no`, or `any`.
    - Sleep Schedule: `early_bird`, `night_owl`, or `flexible`.
    - Occupation: Multi-select from `student`, `garments_worker`, `private_job`, `freelancer`, `other`, `any`.
  - Filter controls rendered in a responsive offcanvas drawer / sidebar matching Mockup 03 with chip groups, active filter counter badge, and reset button.
  - Filters are serializable via URL query parameters for shareability and browser back/forward navigation.
- **Priority**: Must
- **Related Stories**: `024-listing-feed-query`, `027-filter-drawer-and-search-ui`

### FR-3: ListingFeedQuery & Read-Model Abstraction (AD-12)
- **Description**: `ListingFeedQuery.for_viewer(viewer, ...)` serves as the sole entrypoint in the application for retrieving lists of listings for any consumer surface.
- **Acceptance Criteria**:
  - Zero custom ORM filtering or raw queries outside of `ListingFeedQuery`.
  - Executes batch queries with `select_related('author__user')` and `prefetch_related('photos')` to completely eliminate N+1 queries.
  - Automatically invokes `ConsentService.render(viewer, listing)` to construct a projected view:
    - For verified viewers: surfaces author display name, tenure, verified badge, and author lifestyle summary.
    - For unverified / anonymous viewers: surfaces kind, rent, rent_unit, area, and verified badge; sets `email=None` and `phone=None`; replaces lifestyle summary with *"Verify to see lifestyle fit"*.
  - Attaches a precomputed `compatibility_hint: int | None` to each projected listing.
- **Priority**: Must
- **Related Stories**: `024-listing-feed-query`, `025-consent-service-and-projection`

### FR-4: Lifestyle Compatibility Match Heuristic (0–6 Score)
- **Description**: An objective, transparent matching hint indicating how many of 6 lifestyle axes align between the seeker's verified passport and the listing's roommate preferences.
- **Acceptance Criteria**:
  - Computed server-side across 6 specific axes:
    1. **Gender**: `listing.pref_gender in ['any', viewer.passport.profile.gender]`
    2. **Smoking**: `listing.pref_smoking in ['any', viewer.passport.profile.smoking]`
    3. **Sleep**: `listing.pref_sleep in ['flexible', viewer.passport.profile.sleep_schedule]`
    4. **Occupation**: `'any' in listing.pref_occupation` or `viewer.passport.profile.occupation in listing.pref_occupation`
    5. **Area**: `listing.area in viewer.passport.profile.preferred_areas`
    6. **Budget**: `listing.rent_bdt <= viewer.passport.profile.budget_bdt` (or within range)
  - Produces an integer score $X \in [0, 6]$.
  - Rendered on cards and detail pages as *"matches X of 6 preferences"*:
    - When $X \ge 4$, badge/label renders with success color (`--bp-success-fg` / `#15803D`) and filled green dots.
    - When $X < 4$, badge/label renders with muted color (`--bp-muted`) and grey dots.
  - If viewer is anonymous or has no verified passport, renders neutral dots with *"Verify to see lifestyle fit"*.
  - Explicit constraint: No percentage, no star rating, and no algorithmic re-ranking is computed or stored (PRD §4.4, AD-12).
- **Priority**: Must
- **Related Stories**: `024-listing-feed-query`, `026-feed-view-and-card-rendering`

### FR-5: Dedicated Listing Detail Surface
- **Description**: A comprehensive listing detail view at `/listings/<uuid:pk>/` accessible to all viewers, displaying accommodation specifications, photography, and lister attributes.
- **Acceptance Criteria**:
  - Breadcrumb navigation: `Browse > [Area] > [Kind]`.
  - Photo gallery component: Displays full-width primary photo with badge counter (`1 / N`) and clickable thumbnail strip for 1–7 photos.
  - Header & Pricing: Renders accommodation kind (`Seat` or `Room`), canonical Dhaka area, rent amount formatted in taka (`৳X,XXX / [seat|room] / month`), and date posted.
  - Accommodation Details: Renders host notes with full Bengali Unicode support and `lang="bn"` container styling where applicable.
  - Author Card: Renders author display name, verified tenure (e.g. *"Verified for 4 months"*), verified shield checkmark, and lifestyle profile chips.
  - Compatibility Card: For verified seekers, breaks down the 6-axis compatibility checklist (green checkmark for matches, muted dash/x for differences).
  - Preference Checklist: Displays what the lister is looking for (preferred gender, smoking, sleep, occupation).
- **Priority**: Must
- **Related Stories**: `028-listing-detail-view-and-gallery`

### FR-6: Soft-Gated Contact Panel & Audit Logging (AD-3, AD-15)
- **Description**: Lister contact details are conditionally projected based on the viewer's verification status. Verified viewers receive direct contact information, while unverified viewers encounter a locked CTA panel. Every disclosure is recorded.
- **Acceptance Criteria**:
  - **For Verified Viewers** (`request.user.is_authenticated and request.user.passport.status == 'verified'`):
    - Lister's email (`mailto:`) and phone number (`tel:`) are rendered directly inside the sticky contact card.
    - Prominently displays off-platform contact advisory: *"Off-platform contact. Basha Pass doesn't run in-app messaging."*
    - Automatically records an append-only `AuditEntry` with `action='contact_viewed'`, `actor=request.user`, `target_id=listing.id`, and `reason='verified_viewer_reveal'`.
  - **For Unverified or Anonymous Viewers**:
    - Lister's email and phone are completely excluded from the server response HTML (zero PII in DOM or data attributes).
    - Renders the locked contact panel matching Mockup 04: shield lock icon, *"Verify to see contact info. Verification usually takes under 24 hours."*, and a primary CTA button *"Start verification"* linking to `/passports/create/` (or login for anonymous visitors).
- **Priority**: Must
- **Related Stories**: `025-consent-service-and-projection`, `028-listing-detail-view-and-gallery`

### FR-7: Trust & Safety Surfacing
- **Description**: Standard trust and safety signposts advising seekers on safe rental practices and providing an off-platform escalation link.
- **Acceptance Criteria**:
  - Listing detail footer surfaces the Safety Card: *"Safety first · Report this listing if anything feels off."*
  - Links to the official Basha Pass support channel (`mailto:support@bashapass.com` with pre-filled listing ID in subject line).
  - Explicit constraint: No in-app report workflow or automated moderation queue in v1 (PRD §4.6).
- **Priority**: Should
- **Related Stories**: `028-listing-detail-view-and-gallery`

---

## Non-Functional Requirements

### Performance
| Requirement | Metric | Target |
|-------------|--------|--------|
| Feed Latency | p95 response time for filtered feed | < 150ms |
| Detail Latency | p95 response time for listing detail | < 100ms |
| Database Efficiency | Feed and detail view query counts | Fixed (zero N+1 queries) |
| Asset Delivery | Listing thumbnail loading | Lazy-loaded with responsive aspect ratios |

### Scalability
| Requirement | Metric | Target |
|-------------|--------|--------|
| Active Inventory | Feed indexing and pagination | Handles 10,000+ active listings efficiently |
| Query Optimization | Composite database indices | B-Tree on `(archived_at, withdrawn_at, created_at)` and `(area, kind, rent_bdt)` |

### Security & Privacy
| Requirement | Standard | Notes |
|-------------|----------|-------|
| PII Redaction | Server-side DOM exclusion | Unverified viewers never receive lister email or phone in response body |
| Audit Trail | AD-15 Append-only log | Every contact disclosure writes to `AuditEntry` |
| View Projection | AD-3 ConsentService | Views only consume `Projection` objects, never raw model PII |

### Reliability & Standards
| Requirement | Metric | Target |
|-------------|--------|--------|
| Test Coverage | Line / Branch coverage for Intent 005 | > 90% |
| Code Quality | Ruff lint and formatting | 0 errors across all modified/added files |
| Script Support | Bengali Unicode | UTF-8 clean rendering for notes and typography |

---

## Technical Constraints

- **Single ListingFeedQuery Entrypoint (AD-12)**: All feed cards, browse pages, and related listing sections must call `ListingFeedQuery.for_viewer()`.
- **ConsentService Sole Ownership (AD-3)**: All projection transformations must occur in `ConsentService.render(viewer, item)`.
- **Append-only Audit (AD-15)**: Contact reveal events must write via `AuditService.append()` inside an atomic transaction.
- **Brand Consistency**: Styles must adhere strictly to `brand-tokens.css` (`--bp-primary: #0F6E7A`, `--bp-secondary: #C56B4F`, `--bp-success: #16A34A`).

---

## Assumptions & Mitigations

| Assumption | Risk if Invalid | Mitigation |
|------------|-----------------|------------|
| Seeker has filled lifestyle profile if verified | Compatibility score cannot compute all 6 axes | Fallback gracefully to counting only populated axes, treating missing ones as non-matching |
| Browsers support modern CSS aspect ratios | Card photos distort on older devices | Use Bootstrap aspect-ratio utilities and CSS `object-fit: cover` |
| Unverified seekers understand why phone is locked | User frustration or abandonment | Clear explanatory copy: *"Verification usually takes under 24 hours"* with direct CTA |

---

## Open Questions

| Question | Owner | Due Date | Resolution |
|----------|-------|----------|------------|
| How should contact audit logging handle repeated page refreshes? | Inception | 2026-10-31 | Log every distinct view where contact info is rendered to maintain comprehensive audit trail per AD-15. |
