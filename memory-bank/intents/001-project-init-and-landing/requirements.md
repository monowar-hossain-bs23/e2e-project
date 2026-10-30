---
intent: 001-project-init-and-landing
phase: inception
status: complete
created: '2026-10-30T07:31:51Z'
updated: '2026-10-30T07:33:30Z'
---

# Requirements: 001-project-init-and-landing

## Intent Overview

Establish the foundational Django 5.2 application architecture with Poetry, development tooling, and design system tokens, and deliver the responsive public landing page matching `docs/mockups/01-landing.html`. This intent serves as the bedrock for all subsequent bounded contexts (Identity, Verification, Passports, Listings, Audit).

## Business Goals

| Goal | Success Metric | Priority |
|------|----------------|----------|
| Reproducible local development foundation | Clean startup via `poetry run python manage.py runserver` and passing `pytest` suite | Must |
| High-trust public introduction to Basha Pass | Responsive landing page at `GET /` faithfully matching the approved design mockup | Must |
| Preparedness for Identity & Verification features | Clean routing and base templates establishing conventions for upcoming intents | Must |

---

## Functional Requirements

### FR-1: Django Project Foundation & Directory Scaffolding
- **Description**: Initialize the Django 5.2 project structure configured with Poetry, environment variable management via `django-environ`, split settings (`config/settings/base.py`, `dev.py`, `test.py`, `prod.py`), static files handling, and Ruff/pytest configuration.
- **Acceptance Criteria**:
  - `pyproject.toml` defines all required runtime (`django`, `django-environ`, `psycopg`) and development dependencies (`pytest`, `pytest-django`, `ruff`).
  - Project configuration is modularized in `config/` with settings split across `base.py`, `dev.py`, `test.py`, and `prod.py`.
  - `python manage.py check` executes with zero errors.
  - Initial `pytest` test suite passes cleanly.
- **Priority**: Must
- **Related Stories**: 001-project-scaffolding

### FR-2: Base Templates & Design System Token Integration
- **Description**: Establish base HTML layout (`templates/base.html`), partials directory (`templates/basha/partials/`), static asset structure (`static/css/`, `static/js/`, `static/images/`), and core brand styling tokens (Trust Teal `#0F6E7A`, Warm Secondary `#C56B4F`, surface/canvas tokens, typography, button states) matching `docs/mockups/01-landing.html`.
- **Acceptance Criteria**:
  - `base.html` provides standard HTML5 document structure, viewport meta, brand CSS variables, and modular blocks (`{% block content %}`, `{% block extra_head %}`, `{% block extra_js %}`).
  - CSS brand variables exactly match the color palette and elevation tokens from `docs/mockups/01-landing.html`.
  - Bootstrap 5.3 + Bootstrap Icons (or custom CSS overrides) render correctly without console errors or broken styles.
- **Priority**: Must
- **Related Stories**: 002-base-templates-and-design-tokens

### FR-3: Public Landing Page View & Template
- **Description**: Implement the public landing page served at root URL (`/`) using a thin view, registered in the public URL allow-list (`config/urls_public.py`).
- **Acceptance Criteria**:
  - Accessing `GET /` returns HTTP 200 without requiring user authentication.
  - Hero section presents the core value proposition ("Find a verified roommate or mess seat in Dhaka"), search teaser, and action CTAs.
  - Interactive "Tenant Passport" showcase card highlights verified credential features (NID check, selfie match, lifestyle compatibility).
  - "How It Works" 3-step section clearly conveys the workflow (Verify Once, Browse Matches, Connect Off-Platform).
  - Safety & trust explainer panel describes how Basha Pass protects renter privacy and eliminates scam listings.
  - Page is fully responsive across desktop, tablet, and mobile viewports.
- **Priority**: Must
- **Related Stories**: 003-landing-page-view-and-template

### FR-4: Navigation Header & Action Links Wiring
- **Description**: Build the top navigation bar and footer containing the Basha Pass brand mark, anchor navigation links, and authentication action buttons wired to prepare for the Identity intent.
- **Acceptance Criteria**:
  - Navigation header includes Basha Pass logo linking to `/`.
  - Navigation links allow quick scrolling/navigation to key sections ("How It Works", "Trust & Safety").
  - "Log In" and "Sign Up" buttons link to standard authentication endpoints (`/accounts/login/`, `/accounts/signup/`) with appropriate fallback or placeholder views.
  - Footer contains copyright notice, platform disclaimers, and key navigational links.
- **Priority**: Must
- **Related Stories**: 004-navigation-and-footer

---

## Non-Functional Requirements

### Performance
| Requirement | Metric | Target |
|-------------|--------|--------|
| Landing Page Load | Server render time (TTFB) | < 100ms locally |
| Asset Delivery | Total landing page payload (HTML+CSS) | < 300KB (excluding external CDNs) |

### Scalability
| Requirement | Metric | Target |
|-------------|--------|--------|
| Concurrent Public Browsers | Public landing page throughput | Lightweight server-rendered response capable of standard caching |

### Security
| Requirement | Standard | Notes |
|-------------|----------|-------|
| Public URL Isolation | Explicit URL allow-list | Landing page is strictly read-only; no user inputs persisted |
| Security Headers | Django Security Middleware | Clickjacking protection, MIME-type sniffing prevention, XSS filter headers |

### Reliability
| Requirement | Metric | Target |
|-------------|--------|--------|
| Test Coverage | Unit/Integration tests | 100% of views and route configurations covered by automated tests |

---

## Constraints

### Technical Constraints
- **Python / Django**: Python 3.12+ with Django 5.2.
- **Dependency Management**: Managed strictly through Poetry (`pyproject.toml`).
- **Code Standards**: Ruff for linting and formatting (line length 88); pytest for testing.
- **Architecture**: Follows `docs/ARCHITECTURE-SPINE.md` with thin views and modular settings.

### Business Constraints
- **Language**: English-only UI in v1 (Bangla localization deferred to v2 per PRD).
- **Geography**: Dhaka-focused messaging in landing page hero and lifestyle tags.

---

## Assumptions

| Assumption | Risk if Invalid | Mitigation |
|------------|-----------------|------------|
| Bootstrap 5.3 CDN + CSS Custom Properties is acceptable for rapid scaffolding | May require local bundling if offline dev is needed | CDN links are pinned with integrity hashes; can be vendored if needed |
| Auth views will be implemented in subsequent intent | Links to `/accounts/signup/` will 404 until intent 002 | Provide graceful stub or landing route mappings |

---

## Open Questions

| Question | Owner | Due Date | Resolution |
|----------|-------|----------|------------|
| Should authentication route links show a "Coming Soon" toast or simple stub view before intent 002? | Team | During Construction | Simple stub view or standard login/signup url endpoints |
