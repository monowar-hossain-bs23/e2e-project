---
stage: plan
bolt: 002-landing-page-ui
created: 2026-10-30T08:16:42Z
---

## Implementation Plan: 002-landing-page-ui

### Objective
Implement the public Basha Pass landing page served at root `/`, faithfully recreating the visual layout, brand styling, and value proposition from `docs/mockups/01-landing.html`. This includes the responsive navigation header, hero section with search teaser, interactive Tenant Passport showcase card, 3-step "How It Works" guide, trust explainer, footer, and automated integration tests.

### Stories Addressed
- **003-landing-hero-and-passport-showcase**: Hero section, search filter teaser, and Tenant Passport showcase card
- **004-how-it-works-and-navigation**: Navigation navbar, "How It Works" steps, trust panel, and footer

### Deliverables
1. **Core App & View Wiring**:
   - `apps/core/`: Django application managing public static pages.
   - `apps/core/views.py`: `landing_view` serving HTTP 200 with template `basha/landing.html`.
   - `config/urls_public.py`: Map root path `""` (name `landing`) to `landing_view`.
   - `config/settings/base.py`: Register `"apps.core"` in `INSTALLED_APPS`.
2. **Template Architecture & Partials (AD-5)**:
   - `templates/basha/landing.html`: Main landing page extending `templates/base.html`.
   - `templates/basha/partials/navbar.html`: Responsive top navigation with logo, anchor links, and auth CTAs (`/accounts/login/`, `/accounts/signup/`).
   - `templates/basha/partials/passport_preview.html`: Authentic Tenant Passport card with verified status badge, photo gradient, NID verification checklist, and lifestyle tags.
   - `templates/basha/partials/how_it_works.html`: 3-step workflow cards (Verify Once, Browse Matches, Connect Off-Platform).
   - `templates/basha/partials/trust_panel.html`: Security and privacy explainer panel.
   - `templates/basha/partials/footer.html`: Global footer with copyright, links, and Dhaka city focus disclaimer.
3. **Automated Integration Tests**:
   - `tests/test_landing.py`:
     - Test `GET /` returns status code 200.
     - Test `landing.html` template and partials are used.
     - Test presence of headline, search pills, passport card, steps, and navigation links.
     - Test reverse resolution of URL name `landing`.

### Dependencies
- `001-core-foundation`: Base template (`templates/base.html`), brand CSS custom properties (`brand-tokens.css`), and Django test settings.
- External CDNs: Bootstrap 5.3 CSS & JS, Bootstrap Icons 1.11.

### Technical Approach
- Thin view pattern (AD-1): `landing_view` handles HTTP request and returns rendered template.
- Modular partial templates (AD-5): Each visual section is cleanly organized under `templates/basha/partials/` with clear context contracts.
- Exact visual fidelity with `docs/mockups/01-landing.html`: Leverage existing brand tokens (`--bp-primary`, `--bp-secondary`, `--bp-elev-*`, `--bp-grad-*`).
- Auth link preparedness: Navbar CTA buttons point to `/accounts/login/` and `/accounts/signup/` (or anchor fallback) ready for the upcoming Identity/Auth intent.

### Acceptance Criteria
- [ ] `GET /` responds with HTTP 200 without requiring login.
- [ ] Landing page matches the layout and design elements of `docs/mockups/01-landing.html`.
- [ ] All partials (`navbar`, `passport_preview`, `how_it_works`, `trust_panel`, `footer`) render correctly.
- [ ] `poetry run pytest` passes all tests in `tests/test_landing.py`.
- [ ] `poetry run ruff check .` and `poetry run ruff format --check .` report 0 errors.
