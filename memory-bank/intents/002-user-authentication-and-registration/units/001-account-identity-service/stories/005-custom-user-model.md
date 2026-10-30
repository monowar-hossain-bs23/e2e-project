---
id: 005-custom-user-model
unit: 001-account-identity-service
intent: 002-user-authentication-and-registration
status: complete
priority: must
created: '2026-10-30T10:06:00Z'
assigned_bolt: 003-account-identity-service
implemented: true
---

# Story: 005-custom-user-model

## User Story

**As a** system architect and future Basha Pass tenant or staff member  
**I want** a dedicated custom `User` model with UUID4 primary keys and normalized email  
**So that** user accounts are secure, prevent enumeration, and support both tenant and admin actors seamlessly  

## Acceptance Criteria

- [ ] **Given** Django configuration, **When** `AUTH_USER_MODEL = 'accounts.User'` is set, **Then** `apps.accounts.models.User` inherits `AbstractBaseUser` and `PermissionsMixin` with `id: UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`.
- [ ] **Given** user creation, **When** `UserManager.create_user(email, password, display_name)` is invoked, **Then** `email` is normalized to lowercase, `email_verified` defaults to `False`, `is_staff` defaults to `False`, `is_active` defaults to `True`, and timestamps are populated.
- [ ] **Given** superuser creation, **When** `UserManager.create_superuser(email, password)` is invoked, **Then** `is_staff=True` and `is_superuser=True`.
- [ ] **Given** database migrations, **When** `makemigrations` and `migrate` run, **Then** the `accounts_user` table is created with unique index on `email`.

## Technical Notes

- Per user standards: standard Django UUID4 (`uuid.uuid4`) used as primary key.
- Case-insensitivity enforced at model level and manager level via `email = email.strip().lower()`.
- Register model in Django Admin for staff users.

## Dependencies

### Requires
- Core foundation (`001-core-foundation`)

### Enables
- `006-email-verification-token-and-service`
- `008-signup-and-verify-email-views`
- `009-login-logout-and-session-views`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Email with uppercase letters (e.g., `Test@Example.COM`) | Normalized to `test@example.com` before unique validation |
| Missing display name during user creation | Raises `ValueError` |
| Attempting duplicate registration | IntegrityError or validation error caught cleanly |

## Out of Scope

- Passport or NID attachments (owned by `passports` context)
- Phone number storage (out of scope for v1)
