---
id: 002-base-layout-and-design-tokens
unit: 001-core-foundation
intent: 001-project-init-and-landing
status: complete
priority: must
created: '2026-10-30T07:33:30Z'
assigned_bolt: 001-core-foundation
implemented: true
---

# Story: 002-base-layout-and-design-tokens

## User Story

**As a** frontend developer / designer
**I want** a standardized base HTML layout with CSS custom properties matching the Basha Pass brand design tokens
**So that** all views and templates share consistent typography, colors, shadows, and responsive scaffolding

## Acceptance Criteria

- [ ] **Given** any template extending `templates/base.html`, **When** rendered, **Then** all brand tokens (`--bp-primary: #0F6E7A`, `--bp-secondary: #C56B4F`, `--bp-elev-*`, `--bp-btn-*`) are accessible in CSS.
- [ ] **Given** `templates/base.html`, **When** inspected, **Then** Bootstrap 5.3 CSS, Bootstrap Icons, and Inter font are included with SRI/CDN tags.
- [ ] **Given** a child template, **When** defining `{% block content %}`, `{% block title %}`, or `{% block extra_css %}`, **Then** the blocks are correctly placed in the rendered document.
- [ ] **Given** mobile and desktop viewports, **When** resizing, **Then** the viewport meta tag ensures appropriate responsive scaling.

## Technical Notes

- Brand palette from `docs/mockups/01-landing.html`:
  - Primary: `#0F6E7A` (Trust Teal)
  - Secondary: `#C56B4F` (Warm Orange/Brown)
  - Success text: `#15803D`
  - Canvas: `#F4F6F9`, Surface: `#FAFBFD`, Ink: `#0F172A`, Muted: `#5A6878`
  - Elevation tokens: `--bp-elev-card`, `--bp-elev-card-hover`, `--bp-elev-passport-stack`
- Place custom CSS tokens in `static/css/brand-tokens.css` or embedded in `base.html` root.

## Dependencies

### Requires
- `001-django-project-scaffolding`

### Enables
- `003-landing-hero-and-passport-showcase`
- `004-how-it-works-and-navigation`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| CDN failure or slow network | Basic system fonts (-apple-system, BlinkMacSystemFont, Segoe UI) provide readable fallback |

## Out of Scope
- Specific landing page view logic (owned by Unit 2)
