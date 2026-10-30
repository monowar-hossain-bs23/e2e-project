---
unit: 001-core-foundation
intent: 001-project-init-and-landing
phase: inception
status: complete
unit_type: backend
default_bolt_type: simple-construction-bolt
created: '2026-10-30T07:33:30Z'
updated: '2026-10-30T07:33:30Z'
---

# Unit Brief: 001-core-foundation

## Purpose
Establish the foundational runtime configuration, package management, directory layout, development tooling (Ruff, pytest), and base presentation templates with brand design tokens for the Basha Pass application.

## Scope

### In Scope
- Poetry initialization with runtime and development dependencies.
- Modular Django 5.2 configuration in `config/settings/` (`base.py`, `dev.py`, `test.py`, `prod.py`).
- Root URL conf setup and integration with `urls_public.py` allow-list.
- Static assets directory setup (`static/css/`, `static/js/`, `static/images/`).
- Base HTML template (`templates/base.html`) embedding brand tokens (Trust Teal `#0F6E7A`, Warm Secondary `#C56B4F`, fonts, elevations).
- Pytest and Ruff configuration and initial health check tests.

### Out of Scope
- Specific business domain models or database migrations.
- Authentication views or user registration logic (belongs to Identity intent).
- Landing page specific content sections (handled in `002-landing-page-ui`).

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Django Project Foundation & Directory Scaffolding | Must |
| FR-2 | Base Templates & Design System Token Integration | Must |

---

## Domain Concepts

### Key Entities / Configs
| Entity / Config | Description | Attributes |
|-----------------|-------------|------------|
| `Settings` | Environment-aware Django settings | `DEBUG`, `SECRET_KEY`, `DATABASES`, `STATIC_URL`, `MEDIA_ROOT` |
| `BrandTokens` | CSS Custom Properties | `--bp-primary`, `--bp-secondary`, `--bp-surface`, `--bp-elev-*` |

### Key Operations
| Operation | Description | Inputs | Outputs |
|-----------|-------------|--------|---------|
| `check_environment` | Validate Django settings and dependencies | Environment variables | Status 0 or config error |
| `render_base_layout` | Render standard HTML5 shell | View template context | HTML document |

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
| `001-django-project-scaffolding` | Setup Poetry, Django 5.2, split settings, and test harness | Must | ready |
| `002-base-layout-and-design-tokens` | Base HTML template with brand tokens and responsive layout structure | Must | ready |

---

## Dependencies

### Depends On
| Unit | Reason |
|------|--------|
| None | Foundation unit |

### Depended By
| Unit | Reason |
|------|--------|
| `002-landing-page-ui` | Requires base template, settings, and static assets structure |

### External Dependencies
| System | Purpose | Risk |
|--------|---------|------|
| Bootstrap 5.3 CDN | Layout and utility grid classes | Low |
| Bootstrap Icons CDN | Icon fonts | Low |

---

## Technical Context

### Suggested Technology
- Python 3.12+
- Django 5.2 LTS
- Poetry
- Ruff (formatting & linting)
- `pytest` + `pytest-django`

---

## Success Criteria

### Functional
- [ ] `poetry run python manage.py check` runs with 0 errors.
- [ ] `poetry run pytest` passes cleanly.
- [ ] `base.html` includes all required CSS custom properties matching `docs/mockups/01-landing.html`.

### Non-Functional
- [ ] Ruff formatting and linting pass with 0 errors.
- [ ] Settings properly load `.env` variables via `django-environ`.

---

## Bolt Suggestions

| Bolt | Type | Stories | Objective |
|------|------|---------|-----------|
| `001-core-foundation` | simple-construction-bolt | `001-django-project-scaffolding`, `002-base-layout-and-design-tokens` | Scaffold project, config, and base templates |
