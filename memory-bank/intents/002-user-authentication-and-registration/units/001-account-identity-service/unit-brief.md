---
unit: 001-account-identity-service
intent: 002-user-authentication-and-registration
phase: inception
status: complete
created: '2026-10-30T10:05:00Z'
updated: '2026-10-30T10:05:00Z'
unit_type: backend
default_bolt_type: ddd-construction-bolt
---

# Unit Brief: 001-account-identity-service

## Purpose

Implement the core Identity domain aggregate, including the custom `User` model, `EmailVerificationToken` model, `AccountService`, password complexity enforcement, and transactional email token dispatching, serving as the trusted foundation for authentication and authorization across Basha Pass.

## Scope

### In Scope
- Custom `User` model (`apps.accounts.models.User`) extending `AbstractBaseUser` + `PermissionsMixin` with UUID4 primary key and case-insensitive email.
- Custom `UserManager` with `create_user` and `create_superuser`.
- `EmailVerificationToken` model with SHA-256 hashed storage, 5-minute expiry, and single-use flag.
- `AccountService` implementing token issuance, token verification (`secrets.compare_digest`), rate-limiting / resend capping (max 3), and password reset token handling.
- Password complexity validator enforcing 5 mandatory rules (≥8 chars, upper, lower, digit, special symbol).
- Case-insensitive email authentication backend (`CaseInsensitiveModelBackend`).
- Transactional email dispatch for 6-digit OTP verification codes.

### Out of Scope
- Public HTTP view controllers, templates, and HTMX partials (handled in `002-auth-ui-views`).
- SMS or phone verification (deferred).
- Social login / OAuth2 integration.

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Custom User Model & Accounts App Foundation | Must |
| FR-3 | 6-Digit Email Verification Token Generation & Dispatch | Must |
| FR-4 | Token Verification & Account Activation Flow (Service Logic) | Must |
| FR-7 | Password Reset / Recovery Flow (Token & Backend) | Should |

---

## Domain Concepts

### Key Entities
| Entity | Description | Attributes |
|--------|-------------|------------|
| `User` | Core account identity for tenants and staff | `id` (UUID4 PK), `email` (unique, lowercase), `display_name`, `password_hash`, `email_verified`, `is_staff`, `is_active`, `date_joined`, `last_login`, `created_at`, `updated_at` |
| `EmailVerificationToken` | Ephemeral 6-digit OTP issued for email verification | `id` (UUID4 PK), `user_id` (FK User), `token_hash` (SHA-256), `created_at`, `expires_at`, `consumed_at`, `resend_count` |

### Key Operations
| Operation | Description | Inputs | Outputs |
|-----------|-------------|--------|---------|
| `AccountService.register_user` | Creates unverified user and generates initial OTP token | `email`, `password`, `display_name` | `(User, raw_token)` |
| `AccountService.issue_verification_token` | Issues a fresh 6-digit token and emails user | `user` | `{ok: bool, token_id, error?}` |
| `AccountService.verify_email_token` | Validates submitted 6-digit OTP against active token hash | `user`, `raw_token` | `{ok: bool, user, error?}` |
| `AccountService.resend_verification_token` | Resends OTP if under 3-resend attempt cap | `user` | `{ok: bool, attempts_left: int, error?}` |

---

## Story Summary

| Metric | Count |
|--------|-------|
| Total Stories | 3 |
| Must Have | 3 |
| Should Have | 0 |
| Could Have | 0 |

### Stories

| Story ID | Title | Priority | Status |
|----------|-------|----------|--------|
| `005-custom-user-model` | Custom User Model & Accounts App Foundation | Must | Planned |
| `006-email-verification-token-and-service` | Email Verification Token & Account Service | Must | Planned |
| `007-password-validation-and-auth-backend` | Password Complexity Validator & Auth Backend | Must | Planned |

---

## Dependencies

### Depends On
| Unit | Reason |
|------|--------|
| `001-core-foundation` | Requires base Django 5.2 configuration and database setup |

### Depended By
| Unit | Reason |
|------|--------|
| `002-auth-ui-views` | Requires models, services, and forms for authentication views |
| Future Units (`passports`, `listings`) | Requires `User` foreign keys |

### External Dependencies
| System | Purpose | Risk |
|--------|---------|------|
| Django SMTP Backend | Outbound OTP delivery | Medium (uses mock/in-memory in dev/test) |

---

## Technical Context

### Suggested Technology
- Python `secrets` module for cryptographically secure 6-digit generation and constant-time digest comparison.
- `hashlib.sha256` for secure OTP token hashing before database storage.
- Django `AbstractBaseUser` + `PermissionsMixin`.

### Integration Points
| Integration | Type | Protocol |
|-------------|------|----------|
| `AccountService` | Python Service API | In-process calls from presentation views |
| Django Admin | Web GUI | Uses custom `UserAdmin` for staff management |

### Data Storage
| Data | Type | Volume | Retention |
|------|------|--------|-----------|
| `accounts_user` | PostgreSQL Table | 100K+ rows | Indefinite (or 30-day soft-delete grace) |
| `accounts_emailverificationtoken` | PostgreSQL Table | 200K+ rows | Consumed immediately; expires 5 mins |

---

## Constraints

- Primary key is standard UUID4.
- Raw OTP tokens must never be written to database or application logs.
- Maximum 3 resend attempts allowed per user signup.

---

## Success Criteria

### Functional
- [ ] Custom `User` model can be created, saved, and queried case-insensitively.
- [ ] 6-digit OTP tokens expire strictly after 5 minutes and cannot be reused once consumed.
- [ ] 3-resend cap prevents subsequent token issuance.
- [ ] Password validation rejects passwords failing any of the 5 complexity rules.

### Non-Functional
- [ ] Token verification executes in < 50ms using SHA-256 and indexed queries.
- [ ] Zero unhandled exceptions; return clean `{ok, value, error}` service envelopes.

### Quality
- [ ] Test coverage > 90% across `test_models.py`, `test_services.py`, and `test_validators.py`.
- [ ] 100% clean Ruff linting and formatting.

---

## Bolt Suggestions

| Bolt | Type | Stories | Objective |
|------|------|---------|-----------|
| `003-account-identity-service` | DDD | 005, 006, 007 | Implement User aggregate, EmailVerificationToken, AccountService, and auth backend |
