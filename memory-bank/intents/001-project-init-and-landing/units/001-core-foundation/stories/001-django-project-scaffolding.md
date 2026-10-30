---
id: 001-django-project-scaffolding
unit: 001-core-foundation
intent: 001-project-init-and-landing
status: complete
priority: must
created: '2026-10-30T07:33:30Z'
assigned_bolt: 001-core-foundation
implemented: true
---

# Story: 001-django-project-scaffolding

## User Story

**As a** developer working on Basha Pass
**I want** a cleanly structured Django 5.2 project managed with Poetry, split settings, and test configuration
**So that** all team members and AI agents have a consistent, reproducible development and testing baseline

## Acceptance Criteria

- [ ] **Given** a fresh clone, **When** running `poetry install`, **Then** all runtime and development dependencies are installed cleanly.
- [ ] **Given** the repository root, **When** executing `poetry run python manage.py check`, **Then** Django reports no system check issues.
- [ ] **Given** `DJANGO_SETTINGS_MODULE` configured to `config.settings.dev`, **When** the server starts, **Then** environment variables are loaded via `django-environ`.
- [ ] **Given** the test environment, **When** running `poetry run pytest`, **Then** the test suite discovers and executes tests using `pytest-django`.
- [ ] **Given** codebase files, **When** running `poetry run ruff check .` and `poetry run ruff format --check .`, **Then** zero linting or formatting violations are found.

## Technical Notes

- Set up `pyproject.toml` with `poetry.dependencies` (`python = "^3.12"`, `django = "^5.2"`, `django-environ = "^0.11"`, `psycopg = "^3.1"`) and `poetry.group.dev.dependencies` (`pytest`, `pytest-django`, `ruff`).
- Settings structure under `config/settings/`:
  - `base.py`: Installed apps, middleware, templates, auth password validators, internationalization, static/media configuration.
  - `dev.py`: Debug mode enabled, local secret key, SQLite or local Postgres.
  - `test.py`: In-memory database or fast password hashers for testing.
  - `prod.py`: Production security middleware, strict allowed hosts, environment secret key.
- Root URL conf in `config/urls.py` linking to `config/urls_public.py`.

## Dependencies

### Requires
- None

### Enables
- `002-base-layout-and-design-tokens`
- `003-landing-hero-and-passport-showcase`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Missing `.env` file | Falls back to sensible development defaults with warning |
| Missing `SECRET_KEY` in production | Raises `ImproperlyConfigured` exception |

## Out of Scope
- Specific business domain models
- Authentication endpoints implementation
