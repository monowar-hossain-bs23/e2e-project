# Basha Pass

Verified roommate and seat-matching platform for urban Bangladesh.

## Tech Stack
- **Backend / Web**: Python 3.12+, Django 5.2, HTMX
- **Architecture**: Modular Monolith with Django MTV + Service Layer
- **Database**: PostgreSQL (with Django ORM)
- **Tooling**: Poetry, Ruff, pytest

## Quick Start

### 1. Install Dependencies
```bash
poetry install
```

### 2. Environment Setup
```bash
cp .env.example .env
```

### 3. Run Checks & Tests
```bash
poetry run python manage.py check
poetry run pytest
```

### 4. Run Development Server
```bash
poetry run python manage.py runserver
```
