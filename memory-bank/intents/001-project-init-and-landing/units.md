---
intent: 001-project-init-and-landing
phase: inception
status: units-decomposed
updated: 2026-10-30T07:33:30Z
---

# 001-project-init-and-landing - Unit Decomposition

## Units Overview

This intent decomposes into 2 independently verifiable units of work:

### Unit 1: `001-core-foundation`

**Description**: Project scaffolding, Poetry package configuration, modular Django settings, test harness (pytest), Ruff linting/formatting configuration, and base layout template (`templates/base.html`) embedding brand CSS variables and layout blocks.

**Assigned Requirements**:
- FR-1: Django Project Foundation & Directory Scaffolding
- FR-2: Base Templates & Design System Token Integration

**Stories**:
- `001-django-project-scaffolding`: Setup Poetry, Django 5.2, split settings, and test harness
- `002-base-layout-and-design-tokens`: Base HTML template with brand tokens and responsive layout structure

**Deliverables**:
- `pyproject.toml`, `poetry.lock`
- `manage.py`, `config/settings/` (`base.py`, `dev.py`, `test.py`, `prod.py`), `config/urls.py`
- `static/css/brand-tokens.css`
- `templates/base.html`
- `tests/test_scaffolding.py`

**Dependencies**:
- Depends on: None
- Depended by: `002-landing-page-ui`

**Estimated Complexity**: Medium (M)
**Unit Type**: backend
**Default Bolt Type**: `simple-construction-bolt`

---

### Unit 2: `002-landing-page-ui`

**Description**: Public landing page view, routing, templates, and interactive presentation components matching `docs/mockups/01-landing.html`, complete with hero section, Tenant Passport preview card, "How It Works" process flow, safety/trust explainer, top navigation, and footer.

**Assigned Requirements**:
- FR-3: Public Landing Page View & Template
- FR-4: Navigation Header & Action Links Wiring

**Stories**:
- `003-landing-hero-and-passport-showcase`: Hero section, search filter teaser, and Tenant Passport showcase card
- `004-how-it-works-and-navigation`: Navigation navbar, "How It Works" steps, trust panel, and footer

**Deliverables**:
- `apps/core/` (or root landing views and URL routing)
- `config/urls_public.py` registration for root `/`
- `templates/basha/landing.html`
- `templates/basha/partials/` (passport preview, how-it-works cards)
- `tests/test_landing.py`

**Dependencies**:
- Depends on: `001-core-foundation`
- Depended by: None (prepares entry points for future `002-user-authentication` intent)

**Estimated Complexity**: Medium (M)
**Unit Type**: frontend
**Default Bolt Type**: `simple-construction-bolt`

---

## Unit Dependency Graph

```text
[001-core-foundation] ──► [002-landing-page-ui]
```

## Execution Order

1. **Step 1**: `001-core-foundation` (scaffolding, settings, base templates, tokens)
2. **Step 2**: `002-landing-page-ui` (landing page view, partials, components, visual validation)
