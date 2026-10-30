---
id: 008-signup-and-verify-email-views
unit: 002-auth-ui-views
intent: 002-user-authentication-and-registration
status: complete
priority: must
created: '2026-10-30T10:06:00Z'
assigned_bolt: 004-user-auth-ui
implemented: true
---

# Story: 008-signup-and-verify-email-views

## User Story

**As a** prospective tenant visiting Basha Pass  
**I want** a polished, responsive signup page and OTP verification screen matching the design mockups  
**So that** I can register quickly, confirm my email code, and proceed directly to my welcome onboarding screen  

## Acceptance Criteria

- [ ] **Given** a visitor accessing `GET /accounts/signup/`, **When** rendered, **Then** the page displays a responsive 2-column layout on desktop (brand pillar panel on left, registration form on right) matching `docs/mockups/06-signup.html`.
- [ ] **Given** valid submission on `POST /accounts/signup/`, **When** processed, **Then** an unverified user is created, an OTP is dispatched, and the browser redirects to `/accounts/verify-email/`.
- [ ] **Given** a user accessing `GET /accounts/verify-email/`, **When** rendered, **Then** the page displays the 6-digit OTP input interface and resend action matching `docs/mockups/07-verify-email.html`.
- [ ] **Given** a user submitting a valid 6-digit OTP on `POST /accounts/verify-email/`, **When** verified, **Then** the user session is authenticated via `login()`, `user.email_verified` is true, and browser redirects to `/accounts/welcome/`.
- [ ] **Given** an expired token, **When** submitted, **Then** the user is presented with the expired state matching `docs/mockups/13-verify-email-expired.html` or inline error with resend action.
- [ ] **Given** a click on "Resend code", **When** triggered via HTMX (`POST /accounts/verify-email/resend/`), **Then** a new token is dispatched, remaining attempts are updated, and UI reflects countdown without full page reload.
- [ ] **Given** routes `/accounts/signup/` and `/accounts/verify-email/`, **When** evaluated against security rules, **Then** both are allow-listed in `config/urls_public.py` as public URLs.

## Technical Notes

- Uses `SignupForm` inheriting `LocaleFormMixin`.
- Password meter provides real-time client-side feedback matching the 5 rules in mockup.
- Welcome view rendered at `/accounts/welcome/` matching `docs/mockups/11-welcome.html` (full-bleed teal card).

## Dependencies

### Requires
- `005-custom-user-model`
- `006-email-verification-token-and-service`
- `007-password-validation-and-auth-backend`

### Enables
- `009-login-logout-and-session-views`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Visitor navigates directly to `/accounts/verify-email/` without signup session | Redirects to `/accounts/signup/` with helpful message |
| 3-resend limit exceeded | HTMX partial disables button and displays limit reached alert |
| Duplicate email submitted at signup | Displays clear non-technical error: "An account with this email already exists." |

## Out of Scope

- Passport NID upload flow (future intent)
