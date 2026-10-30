---
stage: plan
bolt: 001-core-foundation
created: 2026-10-30T08:02:11Z
---

## Implementation Plan: 001-core-foundation

### Objective
Establish the foundational infrastructure for Basha Pass: initialize Poetry dependencies, scaffold the modular Django 5.2 project architecture with environment-aware split settings, configure Ruff and pytest, and create the base presentation layout with brand design system tokens matching `docs/mockups/01-landing.html`.

### Stories Addressed
- **001-django-project-scaffolding**: Setup Poetry, Django 5.2, split settings, and test harness
- **002-base-layout-and-design-tokens**: Base HTML template with brand tokens and responsive layout structure

### Deliverables
1. **Package Management & Tooling**:
   - `pyproject.toml`: Poetry configuration with Python ^3.12, Django ^5.2, django-environ ^0.11, psycopg ^3.2, pytest, pytest-django, and ruff settings (line length 88).
   - `.env.example`: Template for environment variables (`DEBUG`, `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`).
2. **Project Architecture Scaffolding**:
   - `manage.py`: Django entrypoint referencing `config.settings.dev`.
   - `config/settings/base.py`: Core Django settings (installed apps, middleware, template loaders, internationalization, static/media directories).
   - `config/settings/dev.py`: Development configuration (debug on, console email, local database).
   - `config/settings/test.py`: Fast test configuration (in-memory SQLite test database, fast password hashers).
   - `config/settings/prod.py`: Production hardened settings.
   - `config/urls.py` & `config/urls_public.py`: URL dispatch with explicit public URL allow-list.
   - `config/wsgi.py` & `config/asgi.py`.
3. **Design System & Base Templates**:
   - `static/css/brand-tokens.css`: All brand variables from `docs/mockups/01-landing.html` (Trust Teal `#0F6E7A`, Warm Secondary `#C56B4F`, elevations, button state tokens).
   - `templates/base.html`: Standard HTML5 structure with Bootstrap 5.3 CDN, Bootstrap Icons CDN, Inter font, custom CSS tokens, and template blocks (`title`, `extra_head`, `content`, `extra_js`).
   - `templates/basha/partials/`: Initialized directory for reusable surface partials.
4. **Test Harness**:
   - `tests/conftest.py`: Pytest configuration and fixtures.
   - `tests/test_scaffolding.py`: Unit tests asserting Django settings load, system check passes, and configuration integrity.
   - `tests/test_base_template.py`: Template rendering test verifying brand tokens and block injection.

### Dependencies
- **External CDNs**: Bootstrap 5.3.3 CSS, Bootstrap Icons 1.11.3, Google Fonts (Inter).
- **Python Libraries**: `django`, `django-environ`, `psycopg`, `pytest`, `pytest-django`, `ruff`.

### Technical Approach
- Use `django-environ` in `config/settings/base.py` to seamlessly parse environment variables with secure fallbacks in development.
- Keep `base.py` clean by isolating environment-specific configuration into `dev.py`, `test.py`, and `prod.py`.
- Ensure `manage.py` and pytest default to `config.settings.dev` and `config.settings.test` respectively.
- Follow PEP 8 and project coding standards strictly (enforced via Ruff).
- Follow Architecture Spine AD-5 and AD-8 for template partials and public URL allow-lists.

### Acceptance Criteria
- [ ] `poetry install` installs dependencies cleanly.
- [ ] `poetry run python manage.py check` reports 0 errors.
- [ ] `poetry run ruff check .` and `poetry run ruff format --check .` report 0 issues.
- [ ] `poetry run pytest` discovers and passes all tests in `tests/`.
- [ ] `templates/base.html` accurately incorporates all brand tokens and renders valid HTML5.
