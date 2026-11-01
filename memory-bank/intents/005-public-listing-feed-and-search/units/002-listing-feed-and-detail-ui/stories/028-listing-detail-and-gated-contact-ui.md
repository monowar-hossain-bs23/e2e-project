---
id: 028-listing-detail-and-gated-contact-ui
unit: 002-listing-feed-and-detail-ui
intent: 005-public-listing-feed-and-search
status: complete
priority: must
created: '2026-10-31T16:00:00Z'
assigned_bolt: 010-listing-discovery-and-detail-ui
implemented: true
---

# Story: 028-listing-detail-and-gated-contact-ui

## User Story

**As a** verified prospective tenant
**I want** to view the full listing detail page, browse photos, inspect the lifestyle compatibility checklist, and access lister contact info through a soft-gated panel
**So that** I can reach out directly via phone or email off-platform while preserving mutual trust.

## Acceptance Criteria

- [x] **Given** any viewer visiting `/listings/<uuid:pk>/`, **When** the page renders, **Then** it presents breadcrumbs (`Browse > [Area] > [Kind]`), main photo gallery with primary display and thumbnail selector (1–7 photos), kind badge, formatted rent, Dhaka area, full host notes with Bengali Unicode support, lister profile card, and preference checklist matching [Mockup 04](file:///home/bs01496/Documents/LMS/basa-pass/docs/mockups/04-listing-detail.html).
- [x] **Given** an authenticated viewer holding a verified Tenant Passport (`passport.status == 'verified'`), **When** viewing the detail page, **Then**:
  - The sticky contact card displays lister direct contact channels: email (`mailto:{email}`) and phone (`tel:{phone}`).
  - Displays the off-platform contact notice: *"Off-platform contact. Basha Pass doesn't run in-app messaging."*
  - An append-only `AuditEntry` is created with `action='contact_viewed'`, `actor=request.user`, `target_id=listing.id`, and `reason='verified_viewer_reveal'`.
  - The compatibility card displays the 6-axis checklist showing which preferences match (green checkmark) and differ (muted cross).
- [x] **Given** an unverified user or anonymous visitor, **When** viewing the detail page, **Then**:
  - The contact section renders the locked contact panel matching Mockup 04 (shield lock icon, *"Verify to see contact info. Verification usually takes under 24 hours."*, and primary CTA button *"Start verification"* routing to `/passports/create/` or login).
  - The response HTML DOM contains zero instances of the lister's email address or phone number.
- [x] **Given** the bottom of the sidebar, **When** rendered, **Then** a safety notice card is displayed: *"Safety first · Report this listing if anything feels off."* linking to `mailto:support@bashapass.com?subject=Report%20Listing%20[ID]`.

## Technical Notes

- View implementation: `ListingDetailView(DetailView)` retrieving listing projection via `ListingFeedQuery` / `ConsentService`.
- JavaScript photo thumbnail switcher: updates primary photo src and active thumbnail border.
- Audit entry written in atomic transaction via `AuditService.append()`.

## Dependencies

### Requires
- `024-listing-consent-service-and-projection`
- `025-listing-feed-query-and-compatibility`
- `027-listing-card-and-compatibility-ui`

### Enables
- None (Intent 005 complete)

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Verified user repeatedly refreshes detail page | Each page view emits a `contact_viewed` audit entry ensuring full audit trail |
| Listing is withdrawn or archived while seeker has page open | Direct URL navigation to withdrawn listing returns 404 for public seekers (403 for non-owners) |
| Author views their own listing detail page | Author sees their own contact panel without recording an external seeker audit entry |

## Out of Scope

- In-app messaging, chat, or handshake state machines (PRD §4.5 explicitly out of scope for v1).
- In-app reporting queue or dispute resolution (PRD §4.6 manual moderation).
