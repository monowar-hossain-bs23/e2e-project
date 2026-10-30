---
id: 007-password-validation-and-auth-backend
unit: 001-account-identity-service
intent: 002-user-authentication-and-registration
status: complete
priority: must
created: '2026-10-30T10:06:00Z'
assigned_bolt: 003-account-identity-service
implemented: true
---

# Story: 007-password-validation-and-auth-backend

## User Story

**As a** security-conscious platform operator  
**I want** strict 5-rule password complexity validation and case-insensitive email authentication  
**So that** user accounts are protected against brute-force attacks and credential confusion  

## Acceptance Criteria

- [ ] **Given** a user setting or changing a password, **When** validated by `PasswordComplexityValidator`, **Then** it enforces:
  1. Minimum length of 8 characters
  2. At least one uppercase ASCII letter (`[A-Z]`)
  3. At least one lowercase ASCII letter (`[a-z]`)
  4. At least one numeric digit (`[0-9]`)
  5. At least one special symbol (`[!@#$%^&*(),.?":{}|<>]`)
- [ ] **Given** a password missing any of the 5 rules, **When** validated, **Then** a descriptive `ValidationError` is raised detailing exactly which criteria failed.
- [ ] **Given** a user logging in, **When** submitting email in mixed case (e.g., `User@Domain.com`), **Then** `CaseInsensitiveModelBackend` authenticates against the normalized email address correctly.
- [ ] **Given** Django configuration, **When** session settings are loaded, **Then** `SESSION_COOKIE_AGE = 2592000` (30 days), `SESSION_COOKIE_HTTPONLY = True`, and `SESSION_COOKIE_SAMESITE = 'Lax'`.

## Technical Notes

- Register `PasswordComplexityValidator` in `AUTH_PASSWORD_VALIDATORS` in `config/settings/base.py`.
- Custom backend subclasses `django.contrib.auth.backends.ModelBackend`.
- Expose password rule evaluation helper function for client-side and form-level UI validation.

## Dependencies

### Requires
- `005-custom-user-model`

### Enables
- `008-signup-and-verify-email-views`
- `009-login-logout-and-session-views`
- `010-password-reset-views`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Password with 7 characters meeting all other 4 rules | Fails with minimum length error |
| Password with 20 characters but no special symbol | Fails with missing symbol error |
| Non-ASCII / Bengali characters in password | Validated gracefully alongside required ASCII classes |

## Out of Scope

- Multi-factor authentication (MFA) / TOTP authenticator apps (v2)
