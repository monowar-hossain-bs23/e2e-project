---
stage: plan
bolt: 004-user-auth-ui
created: '2026-10-30T12:32:00Z'
---

# Implementation Plan: 002-auth-ui-views

## Objective
Implement responsive, user-friendly authentication and onboarding views, forms, templates, and HTMX partials matching the approved design mockups (`06-signup.html`, `07-verify-email.html`, `08-login.html`, `09-forgot-password-request.html`, `10-forgot-password-confirm.html`, `11-welcome.html`), fully integrating with `AccountService` and Architecture Spine AD-8 route protections.

---

## Deliverables

### 1. Forms (`apps/accounts/forms.py`)
- `SignupForm`: Email, display name, password; incorporates `PasswordComplexityValidator` and case-insensitive uniqueness checks.
- `VerifyEmailForm`: 6-digit OTP code input.
- `LoginForm`: Email and password with case-insensitive authentication.
- `PasswordResetRequestForm`: Email lookup for password recovery.
- `SetNewPasswordForm`: Password and confirmation with complexity checks.

### 2. Views (`apps/accounts/views.py`)
- `SignupView` (`/accounts/signup/`): Renders 2-column layout; invokes `AccountService.register_user`; redirects to `/accounts/verify-email/`.
- `VerifyEmailView` (`/accounts/verify-email/`): Validates submitted code via `AccountService.verify_email_token`; establishes 30-day authenticated session; redirects to `/accounts/welcome/`.
- `ResendOTPView` (`/accounts/verify-email/resend/`): HTMX endpoint invoking `AccountService.resend_verification_token`; updates attempts badge dynamically.
- `LoginView` (`/accounts/login/`): Authenticates credentials; redirects unverified tenants to verify email; sets 30-day session cookie; redirects to `?next=` or default landing.
- `LogoutView` (`/accounts/logout/`): Invalidates session immediately.
- `WelcomeView` (`/accounts/welcome/`): Post-verification full-bleed teal landing screen (`LoginRequiredMixin`).
- `PasswordReset*` views: Full self-service recovery flow.

### 3. Templates & Partials
- Layout: `templates/accounts/auth_base.html` (reusable split pane with brand hero).
- Pages: `signup.html`, `verify_email.html`, `login.html`, `welcome.html`, `password_reset.html`, `password_reset_confirm.html`.
- Partials: `templates/accounts/partials/resend_status.html`.
- Stylesheet: `static/css/auth.css` leveraging `brand-tokens.css` variables.

### 4. Routing & Protection
- `apps/accounts/urls.py` registered in `config/urls.py`.
- `config/urls_public.py` updated to include public auth URLs.

---

## Dependencies
- `001-core-foundation`: Base design system tokens (`brand-tokens.css`), Bootstrap 5.3 + HTMX 2.0.4.
- `003-account-identity-service`: `User`, `EmailVerificationToken`, and `AccountService`.

---

## Technical Approach
- Leverage Django Class-Based Views (`FormView`, `View`, `TemplateView`) for clean lifecycle handling.
- Use HTMX for instant feedback on OTP resend without full-page reloads.
- Client-side vanilla JavaScript for real-time password meter strength visualization, accompanied by server-side validation.
- Responsive CSS media queries collapsing desktop 2-column split pane into single column on mobile (<768px).

---

## Acceptance Criteria
- [ ] Signup form enforces 5-rule password complexity and unique email.
- [ ] OTP verification screen validates 6-digit code and authenticates user into session.
- [ ] Resend button via HTMX decrements remaining attempts and disables at 0.
- [ ] Login persists session for 30 days and blocks unverified tenants with redirect.
- [ ] Logout invalidates session immediately.
- [ ] All views match mockups and brand tokens.
- [ ] Test suite covers all view endpoints and happy/unhappy paths.
