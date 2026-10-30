---
stage: implement
bolt: 001-core-foundation
created: 2026-10-30T08:11:30Z
---

## Implementation Walkthrough: 001-core-foundation

### Summary

Established the foundational infrastructure, package dependencies, environment-aware split settings, and test harness for Basha Pass. Created the base presentation layout template incorporating the complete brand design tokens and elevation systems matching the platform design guidelines.

### Structure Overview

The project is structured as a modular Django application with configuration isolated inside the `config/` directory. Settings are cleanly separated across environment roles (`base.py`, `dev.py`, `test.py`, `prod.py`), while static files and templates provide the visual presentation layer. Automated quality gates are enforced via Ruff and pytest-django.

### Completed Work

- [x] `pyproject.toml` - Defines Poetry dependencies, Ruff lint/format rules, and pytest runner configuration.
- [x] `README.md` - Provides setup instructions, architecture summary, and developer command references.
- [x] `.env.example` - Declares template configuration variables for security, debug status, and databases.
- [x] `.gitignore` - Prevents accidental tracking of virtual environments, cache files, and private PII media.
- [x] `manage.py` - Standard Django command-line execution entrypoint defaulting to development settings.
- [x] `config/settings/base.py` - Core Django settings, installed apps, middleware, template engine, and PII storage paths.
- [x] `config/settings/dev.py` - Development configuration with debug mode enabled and console email backend.
- [x] `config/settings/test.py` - Accelerated testing configuration with in-memory database and fast password hashing.
- [x] `config/settings/prod.py` - Production security hardening, HSTS configuration, and secure session flags.
- [x] `config/urls.py` - Root URL routing including Django admin and delegating public URLs.
- [x] `config/urls_public.py` - Public route allow-list per Architecture Spine invariant AD-8.
- [x] `config/wsgi.py` - WSGI entrypoint for web servers.
- [x] `config/asgi.py` - ASGI entrypoint for asynchronous gateways.
- [x] `static/css/brand-tokens.css` - Custom CSS variables for brand colors (Trust Teal, Warm Secondary), button states, and elevations.
- [x] `templates/base.html` - Standard HTML5 presentation shell with Inter font, Bootstrap 5.3 CDN, icons, and template blocks.
- [x] `templates/basha/partials/.gitkeep` - Directory structure for reusable template partials (AD-5).
- [x] `media/private/.gitkeep` - Isolated filesystem path for private verification PII documents (AD-9).
- [x] `media/public/.gitkeep` - Filesystem path for public media assets.
- [x] `tests/conftest.py` - Pytest configuration and database fixtures.
- [x] `tests/test_scaffolding.py` - Automated tests verifying system check, settings variables, and admin routing.
- [x] `tests/test_base_template.py` - Automated tests verifying base template rendering and block overrides.

### Key Decisions

- **Poetry Package Management**: Configured with `package-mode = false` to manage application dependencies without packaging the repository as an installable Python distribution.
- **Settings Split**: Decoupled environment-specific configurations into separate modules rather than monolithic boolean branching inside a single file.
- **PII Storage Root Separation**: Explicitly defined `MEDIA_PRIVATE_ROOT` and `MEDIA_PUBLIC_ROOT` to adhere strictly to Architecture Spine AD-9.
- **CSS Token Architecture**: Maintained Bootstrap 5.3 compatibility while repainting default component styling using brand custom properties.

### Deviations from Plan

- Adjusted Poetry `requires-python` constraint to `">=3.12,<4"` to satisfy `django-environ` dependency range requirements.

### Dependencies Added

- [x] `django` - Core web framework.
- [x] `django-environ` - Twelve-factor environment configuration parser.
- [x] `psycopg[binary]` - PostgreSQL database adapter.
- [x] `pytest` - Test execution framework.
- [x] `pytest-django` - Django test integration and fixtures.
- [x] `ruff` - Python linter and code formatter.

### Developer Notes

- Always execute tests via `poetry run pytest` which automatically targets `config.settings.test`.
- Run `poetry run ruff check .` and `poetry run ruff format .` prior to committing changes.
