---
id: 004-how-it-works-and-navigation
unit: 002-landing-page-ui
intent: 001-project-init-and-landing
status: complete
priority: must
created: '2026-10-30T07:33:30Z'
assigned_bolt: 002-landing-page-ui
implemented: true
---

# Story: 004-how-it-works-and-navigation

## User Story

**As a** prospective renter or room lister
**I want** a clear 3-step "How It Works" guide, a safety explainer, a responsive top navigation bar, and footer links
**So that** I feel confident in the platform's security and can easily navigate to sign up or log in

## Acceptance Criteria

- [ ] **Given** the top navbar, **When** viewed on desktop, **Then** it presents the Basha Pass logo linking to `/`, navigation links ("How It Works", "Find a Roommate"), and CTAs ("Log In", "Get Started").
- [ ] **Given** the top navbar on mobile, **When** tapping the hamburger toggle, **Then** the menu expands smoothly with all navigation items accessible.
- [ ] **Given** the "How It Works" section, **When** viewed, **Then** 3 numbered step cards describe:
  - Step 1: Verify Once (Upload NID & Selfie).
  - Step 2: Browse Matches (Filter by verified traits & location).
  - Step 3: Connect Off-Platform (Direct contact via phone/WhatsApp).
- [ ] **Given** the Trust & Privacy section, **When** viewed, **Then** it clearly explains that sensitive NID documents are never publicly exposed or shared with strangers.
- [ ] **Given** the footer, **When** scrolled to bottom, **Then** brand copyright, quick links, and Dhaka city focus disclaimer are visible.
- [ ] **Given** automated tests in `tests/test_landing.py`, **When** executed, **Then** they verify `GET /` returns status 200, checks response content for hero, steps, and navigation.

## Technical Notes

- Navigation header and footer can be integrated in `templates/base.html` or as partials (`templates/basha/partials/navbar.html`, `templates/basha/partials/footer.html`).
- Auth CTA links point to `reverse('accounts:login')` and `reverse('accounts:signup')` with graceful fallback or placeholders if the accounts app routes are not yet registered.

## Dependencies

### Requires
- `003-landing-hero-and-passport-showcase`

### Enables
- Next intent: `002-user-authentication`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| JavaScript disabled | Responsive CSS fallback allows content and links to remain fully readable |

## Out of Scope
- Backend authentication logic or verification document processing
