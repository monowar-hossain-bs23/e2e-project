# Tech Stack

## Overview
Basha Pass is built as a server-rendered web platform using Python with Django (MTV + HTMX partials) and an explicit service layer, managed with Poetry. This provides rapid development, robust data modeling, and seamless single-page-app-like interactions without the overhead of a separate frontend SPA.

## Languages
Python (3.12+)

**Rationale**: Python offers strong ecosystem maturity, excellent ORM capabilities in Django, and concise syntax. Type hints (`typing`, `mypy`) will be used across services and domain models to ensure safety and maintainability.

## Framework
Django (with HTMX for reactive partial rendering)

**Rationale**:
- Follows the Django MTV pattern extended with a dedicated service layer (per `docs/ARCHITECTURE-SPINE.md`).
- HTMX handles dynamic frontend interactions (filtering, partial updates, inline forms) keeping views thin HTTP adapters.
- Django's built-in Admin serves as the verification and management surface for administrators.

## Authentication
Stock Django Auth + Email 6-digit OTP Token

**Rationale**:
- Admin authentication uses stock Django admin (`is_staff=True`).
- Tenant authentication uses email-based signup/login with 6-digit verification tokens (5-minute expiry) and password policy, as specified in the Architecture Spine (FR-1, FR-20, AD-8).

## Infrastructure & Deployment
TBD (Decided during Operations phase)

**Rationale**:
- Initial local development with Docker / local virtual environments. Production containerization and hosting environment to be finalized during the Operations phase.

## Package Manager
Poetry

**Rationale**:
- Provides deterministic dependency resolution (`poetry.lock`), virtual environment isolation, and clean packaging.

## Decision Relationships
- **Django + HTMX**: Eliminates the need for a separate Node/React frontend build pipeline while delivering interactive UX.
- **Django Auth + Service Layer**: Preserves Django's security defaults while enforcing domain invariants (e.g., passport state transitions, cooldowns) through `VerificationService` and `AccountService`.
