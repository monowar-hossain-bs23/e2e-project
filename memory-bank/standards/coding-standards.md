# Coding Standards

## Overview
Coding standards for Basha Pass. These standards guide human developers and AI agents in writing consistent, idiomatic, and maintainable Python/Django code with an explicit service layer.

## Formatting & Linting
- **Tool**: Ruff (formatting + linting)
- **Line Length**: 88 characters
- **Ruleset**: Standard Ruff defaults + import sorting (I) + code modernization (UP) + bugbear (B)
- **Indentation**: 4 spaces (standard PEP 8)
- **Strings**: Double quotes preferred

## Naming Conventions
- **Variables & Functions**: `snake_case` (e.g., `user_profile`, `get_active_listings`)
- **Classes & Models**: `PascalCase` (e.g., `ListingService`, `Passport`, `VerificationStatus`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_ACTIVE_LISTINGS`, `TOKEN_EXPIRY_MINUTES`)
- **Modules & Files**: `snake_case.py` (e.g., `account_service.py`, `models.py`)
- **Private Helpers**: Leading underscore (e.g., `_hash_token`, `_calculate_compatibility`)

## File Organization
- **Pattern**: Domain-driven modular Django apps with thin HTTP adapters and a dedicated service layer (per Architecture Spine AD-1).
- **Structure**:
```text
apps/
  accounts/         # Identity, custom user model, auth views
  verifications/    # Passport creation, verification state machine, admin review
  listings/         # Housing listings, photos, filters, feed
services/
  account/          # Account & session logic
  verification/     # VerificationService (sole state machine mutator)
  consent/          # Redaction & privacy projection
  listing/          # ListingService (archive/cap invariants)
  audit/            # AuditService (append-only ledger)
templates/          # Django MTV + HTMX partials
static/             # CSS (Tailwind), JS (HTMX)
tests/              # pytest test suite
```
- **Conventions**:
  - Views are thin HTTP adapters: parse request, call one service method, return rendered template or HTMX partial.
  - Business logic, validation of business rules, and state transitions belong exclusively in services.

## Testing Strategy
- **Framework**: `pytest` + `pytest-django`
- **Conventions**:
  - Tests located in `tests/` or modular `tests/` within apps.
  - Test function names: `test_<action>_<expected_result>` (e.g., `test_resubmit_before_cooldown_fails`).
  - Arrange-Act-Assert (AAA) pattern.
  - Use pytest fixtures and factories for test data generation.
  - Test business logic comprehensively at the service level; test views with client/request tests verifying HTTP status and rendered partials.

## Error Handling
- **Pattern**: Domain-specific exceptions raised by services and caught by views/handlers.
- **Custom Errors**: Domain exception classes (e.g., `CooldownActiveError`, `InvalidStateTransitionError`, `QuotaExceededError`) with user-friendly messages or error codes.
- **View Handling**: Thin views catch domain exceptions and render contextual error alerts or HTMX fragments, never exposing internal tracebacks.

## Logging & Security
- **Tool**: Python standard `logging` library.
- **Levels**:
  - `DEBUG`: Local development insights and verbose query/adapter debugging.
  - `INFO`: Key domain events (e.g., passport submitted, listing created, verification approved).
  - `WARNING`: Recoverable failures (e.g., rate limit hit, invalid token attempt).
  - `ERROR`: Unhandled exceptions, service degradation, or audit write failures.
- **Security Rules**:
  - **NEVER log PII or sensitive credentials**: Passwords, 6-digit OTP tokens, NID documents/numbers, and raw selfies must never appear in log outputs.
  - Append-only audit trail (`AuditService`) handles security-critical state changes in the database transaction.
