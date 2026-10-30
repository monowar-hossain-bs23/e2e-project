---
unit: 002-auth-ui-views
intent: 002-user-authentication-and-registration
phase: inception
status: complete
created: '2026-10-30T10:05:00Z'
updated: '2026-10-30T10:05:00Z'
unit_type: frontend
default_bolt_type: simple-construction-bolt
---

# Unit Brief: 002-auth-ui-views

## Purpose

Deliver the user-facing authentication views, forms, and responsive templates matching approved design mockups (`06-signup.html`, `07-verify-email.html`, `08-login.html`, `09-forgot-password-request.html`, `10-confirm.html`, `11-welcome.html`), with 30-day session management, HTMX interactive states, and route security via `urls_public.py`.

## Scope

### In Scope
- Signup view (`/accounts/signup/`) with real-time password strength meter and validation feedback.
- Email verification view (`/accounts/verify-email/`) with 6-digit OTP input, 5-minute countdown UI, and HTMX resend trigger.
- Login view (`/accounts/login/`) with 30-day session persistence and unverified redirect guard.
- Authenticated logout endpoint (`POST /accounts/logout/`).
- Password reset request and confirmation views (`/accounts/password-reset/`).
- Welcome screen (`/accounts/welcome/`) welcoming newly verified tenants.
- Public route registrations in `config/urls_public.py`.
- Integration tests simulating visitor browser interactions.

### Out of Scope
- Direct raw SQL queries (all business operations invoke `AccountService`).
- Tenant passport submission or NID upload wizard (handled in future intent).

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-2 | Email-based Visitor Signup & Password Complexity (UI/Form) | Must |
| FR-4 | Token Verification & Account Activation Flow (View & UX) | Must |
| FR-5 | User Login with Session Persistence (30 Days) | Must |
| FR-6 | User Logout | Must |
| FR-7 | Password Reset / Recovery Flow (Views & Templates) | Should |
| FR-8 | Responsive Auth Templates & Design System Parity | Must |

---

## Domain Concepts

### Key Views & Forms
| View / Component | Route | Description |
|------------------|-------|-------------|
| `SignupView` | `/accounts/signup/` | Form taking email, display name, password; triggers OTP dispatch |
| `VerifyEmailView` | `/accounts/verify-email/` | Form taking 6-digit OTP; validates and authenticates session |
| `ResendOTPView` | `/accounts/verify-email/resend/` | HTMX endpoint triggering token resend (max 3) |
| `LoginView` | `/accounts/login/` | Email + password login with 30-day session cookie |
| `LogoutView` | `/accounts/logout/` | Flushes session and redirects to landing |
| `WelcomeView` | `/accounts/welcome/` | Post-verification welcome landing page |
| `PasswordResetView` | `/accounts/password-reset/` | Request password reset email |
| `PasswordResetConfirmView` | `/accounts/password-reset/confirm/<uidb64>/<token>/` | Set new password with complexity enforcement |

---

## Story Summary

| Metric | Count |
|--------|-------|
| Total Stories | 3 |
| Must Have | 2 |
| Should Have | 1 |
| Could Have | 0 |

### Stories

| Story ID | Title | Priority | Status |
|----------|-------|----------|--------|
| `008-signup-and-verify-email-views` | Visitor Signup & Verify Email UI Views | Must | Planned |
| `009-login-logout-and-session-views` | Login, Logout & 30-Day Session Views | Must | Planned |
| `010-password-reset-views` | Password Reset Request & Confirmation UI | Should | Planned |

---

## Dependencies

### Depends On
| Unit | Reason |
|------|--------|
| `001-account-identity-service` | Requires `User`, `EmailVerificationToken`, and `AccountService` |
| `001-core-foundation` | Requires base template, CSS tokens, and public URL allow-list |

### Depended By
| Unit | Reason |
|------|--------|
| Future Intent (`passports`) | Passport wizard redirects unauthenticated visitors to login |

---

## Technical Context

### Suggested Technology
- Django Class-Based Views (`FormView`, `View`, `TemplateView`).
- HTMX 2.0.4 for inline OTP resend and real-time password meter evaluation.
- Design tokens defined in `static/css/brand-tokens.css`.

### Integration Points
| Integration | Type | Protocol |
|-------------|------|----------|
| `config/urls.py` | URLconf | Includes `apps.accounts.urls` |
| `config/urls_public.py` | Allow-list | Exposes signup, verify, login, and reset URLs |

---

## Constraints

- Desktop view features 2-column split (teal brand pane left, form right); collapses gracefully on mobile (<768px).
- Authenticated routes enforce `LoginRequiredMixin`.
- HTMX partials adhere to AD-5 single partial contract.

---

## Success Criteria

### Functional
- [ ] Visitor can register, receive OTP, submit OTP, and land on welcome page authenticated.
- [ ] Registered user can log in and remain logged in across browser restarts (30-day cookie).
- [ ] User can log out and immediately lose authenticated access to protected pages.
- [ ] HTMX resend button properly disables when 3-attempt limit is reached.

### Non-Functional
- [ ] Pages render under 100ms server response time.
- [ ] 100% responsive and accessible markup conforming to WCAG AA contrast standards.

### Quality
- [ ] Integration tests verify all view response codes, form errors, and session state changes.
- [ ] 100% clean Ruff lint and format check.

---

## Bolt Suggestions

| Bolt | Type | Stories | Objective |
|------|------|---------|-----------|
| `004-user-auth-ui` | Simple | 008, 009, 010 | Implement forms, views, URL routing, templates, and HTMX partials |
