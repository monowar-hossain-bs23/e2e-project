---
unit: 002-landing-page-ui
intent: 001-project-init-and-landing
phase: inception
status: complete
unit_type: frontend
default_bolt_type: simple-construction-bolt
created: '2026-10-30T07:33:30Z'
updated: '2026-10-30T07:33:30Z'
---

# Unit Brief: 002-landing-page-ui

## Purpose
Implement the public, responsive landing page for Basha Pass matching `docs/mockups/01-landing.html`, highlighting the core value proposition of verified roommate and seat matching in Dhaka, featuring the Tenant Passport preview, 3-step workflow, safety explainer, responsive navbar, and footer.

## Scope

### In Scope
- Public landing page view (thin HTTP view) and route mapped to root `/`.
- Public routing configuration in `config/urls_public.py`.
- Full landing page template (`templates/basha/landing.html`) inheriting from `templates/base.html`.
- Landing page partials:
  - Hero section with headline and search/filter teaser.
  - Interactive/visual Tenant Passport showcase card with verified badge and lifestyle attributes.
  - "How It Works" 3-step explainer (Verify, Browse, Connect).
  - Safety & trust explainer panel.
  - Social proof & statistics counter.
  - Navigation bar and footer with links wired to `/accounts/` endpoints.
- Integration tests asserting HTTP 200, correct template rendering, and key copy/elements.

### Out of Scope
- Actual live search query execution (deferred to Listing feed intent).
- Actual account creation/login processing (deferred to Identity intent).

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-3 | Public Landing Page View & Template | Must |
| FR-4 | Navigation Header & Action Links Wiring | Must |

---

## Domain Concepts

### Key View Projections & Mock Data
| Component | Description | Elements |
|-----------|-------------|----------|
| `HeroSection` | Top introduction and search teaser | Headline, subtitle, search pills (area, budget), CTAs |
| `PassportShowcase` | Visual representation of a verified passport | Avatar, verification badge, lifestyle tags (non-smoker, student, etc.) |
| `HowItWorks` | 3-step guide | Step 1 (Verify), Step 2 (Browse), Step 3 (Connect Off-Platform) |
| `TrustPanel` | Safety and anti-scam explanation | Privacy guarantees, police verification alignment |

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
| `003-landing-hero-and-passport-showcase` | Hero section, search filter teaser, and Tenant Passport showcase card | Must | ready |
| `004-how-it-works-and-navigation` | Navigation navbar, "How It Works" steps, trust panel, and footer | Must | ready |

---

## Dependencies

### Depends On
| Unit | Reason |
|------|--------|
| `001-core-foundation` | Requires base template, brand CSS tokens, and settings |

### Depended By
| Unit | Reason |
|------|--------|
| None | Public surface ready for upcoming user journey intents |

---

## Technical Context

### Suggested Technology
- Django template engine (MTV)
- HTMX (prepared for future interactive filtering)
- Bootstrap 5.3 + custom brand token styling
- `pytest` + `pytest-django`

---

## Success Criteria

### Functional
- [ ] `GET /` returns HTTP 200 with complete rendered HTML.
- [ ] Visual fidelity matches `docs/mockups/01-landing.html`.
- [ ] All CTAs link to valid target anchors or prepared `/accounts/` routes.
- [ ] Responsive navigation works smoothly on mobile and desktop.

### Non-Functional
- [ ] Zero layout shift or styling breakage.
- [ ] Test suite verifies view status and content presence.

---

## Bolt Suggestions

| Bolt | Type | Stories | Objective |
|------|------|---------|-----------|
| `002-landing-page-ui` | simple-construction-bolt | `003-landing-hero-and-passport-showcase`, `004-how-it-works-and-navigation` | Implement landing page views, templates, and integration tests |
