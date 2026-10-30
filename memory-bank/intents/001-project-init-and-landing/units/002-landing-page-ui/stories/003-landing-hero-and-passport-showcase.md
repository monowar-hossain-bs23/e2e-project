---
id: 003-landing-hero-and-passport-showcase
unit: 002-landing-page-ui
intent: 001-project-init-and-landing
status: complete
priority: must
created: '2026-10-30T07:33:30Z'
assigned_bolt: 002-landing-page-ui
implemented: true
---

# Story: 003-landing-hero-and-passport-showcase

## User Story

**As a** prospective renter visiting the Basha Pass homepage
**I want** to see an engaging hero section with the core value proposition and a visual Tenant Passport card preview
**So that** I immediately understand how Basha Pass makes finding a roommate or seat in Dhaka safe, verified, and hassle-free

## Acceptance Criteria

- [ ] **Given** a visitor navigates to `GET /`, **When** the page loads, **Then** the hero headline clearly communicates "Find a verified roommate or mess seat in Dhaka — without the street grind".
- [ ] **Given** the hero section, **When** viewed on desktop or mobile, **Then** a search & filter teaser is displayed with pills for Area (Dhanmondi, Mirpur, Banani, Bashundhara) and Rent budget.
- [ ] **Given** the Tenant Passport showcase card, **When** rendered, **Then** it displays an authentic preview showing:
  - Verified Tenant pill with shield-check icon.
  - Verification badges: NID Verified, Photo Matched, Police-Form Ready.
  - Lifestyle compatibility traits (e.g. "Non-smoker", "Student", "Early bird").
- [ ] **Given** primary CTA buttons ("Find a Roommate", "List a Seat / Room"), **When** clicked, **Then** they navigate to the appropriate target section or signup path.

## Technical Notes

- Template: `templates/basha/landing.html` and partial `templates/basha/partials/passport_preview.html`.
- View: `apps/core/views.py::landing_view` mapped in `config/urls_public.py`.
- Ensure radial gradients (`--bp-grad-hero-radial-primary`, `--bp-grad-hero-radial-secondary`) match the visual mockup `docs/mockups/01-landing.html`.

## Dependencies

### Requires
- `001-django-project-scaffolding`
- `002-base-layout-and-design-tokens`

### Enables
- `004-how-it-works-and-navigation`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Small mobile screen (<375px) | Passport card stacks neatly below the hero copy without overflowing horizontal viewport |

## Out of Scope
- Dynamic database-driven listing search queries (handled in future listing intent)
