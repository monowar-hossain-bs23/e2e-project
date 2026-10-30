---
id: 009-login-logout-and-session-views
unit: 002-auth-ui-views
intent: 002-user-authentication-and-registration
status: complete
priority: must
created: '2026-10-30T10:06:00Z'
assigned_bolt: 004-user-auth-ui
implemented: true
---

# Story: 009-login-logout-and-session-views

## User Story

**As an** existing registered tenant  
**I want** to log in securely with my email and password and remain logged in across visits  
**So that** I don't have to repeatedly re-enter credentials on my trusted device  

## Acceptance Criteria

- [ ] **Given** a visitor accessing `GET /accounts/login/`, **When** rendered, **Then** the page matches `docs/mockups/08-login.html` with responsive branding pane and login form.
- [ ] **Given** valid credentials on `POST /accounts/login/`, **When** user email is verified, **Then** authenticated session is created, 30-day session cookie is set, and user is redirected to `?next=` destination (if safe) or `/dashboard/`.
- [ ] **Given** an unverified user logging in with correct credentials, **When** submitted, **Then** the view redirects to `/accounts/verify-email/` with a notification to verify email first.
- [ ] **Given** invalid credentials, **When** submitted, **Then** view re-renders with error message "Invalid email or password" without disclosing user existence.
- [ ] **Given** an authenticated user submitting `POST /accounts/logout/`, **When** processed, **Then** the session is immediately invalidated, cookie is cleared, and user is redirected to `/`.
- [ ] **Given** routes `/accounts/login/` and `/accounts/logout/`, **When** configured, **Then** login is in `config/urls_public.py` and logout requires CSRF token protection.

## Technical Notes

- `LoginForm` uses Django's authentication helpers and `CaseInsensitiveModelBackend`.
- Enforces `redirect_authenticated_user = True` on login view so logged-in users are forwarded automatically.

## Dependencies

### Requires
- `005-custom-user-model`
- `007-password-validation-and-auth-backend`

### Enables
- Future authenticated feature views (Passports, Listings, Feeds)

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Inactive user (`is_active=False`) | Login fails with appropriate error |
| Malicious open redirect in `?next=https://evil.com` | Ignored; falls back to default safe URL |
| Submitting with empty email or password | Form validation flags required fields |

## Out of Scope

- "Remember me" checkbox toggling variable expiry (fixed at 30 days per PRD §4.1)
