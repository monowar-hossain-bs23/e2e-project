---
stage: implement
bolt: 004-user-auth-ui
created: '2026-10-30T12:40:00Z'
---

# Implementation Walkthrough: 002-auth-ui-views

## Summary
Constructed the responsive authentication, onboarding, and self-service password recovery user interface for Basha Pass. Implemented clean forms, class-based views, modular templates with design tokens, real-time password strength meter, 6-digit OTP verification UI with HTMX resend trigger, and public route protection conforming to Architecture Spine AD-8.

## Structure Overview
The presentation layer is contained in `apps/accounts/` and `templates/accounts/`. Forms inherit Django Form primitives and bind `PasswordComplexityValidator`. Views inherit Class-Based Views and delegate business logic to `AccountService`. Templates reuse `auth_base.html` for a responsive split-pane layout matching approved design mockups.

## Completed Work

- [x] `static/css/auth.css` - Custom stylesheet for split-pane auth shell, password strength meter, OTP inputs, welcome card, and responsive mobile collapse.
- [x] `apps/accounts/forms.py` - User-facing form definitions for signup, OTP verification, login, password reset request, and password reset confirmation.
- [x] `apps/accounts/views.py` - Class-based HTTP views for visitor registration, email verification, HTMX OTP resend, session login (30 days), logout, welcome, and password recovery.
- [x] `apps/accounts/urls.py` - Route declarations for all account surfaces.
- [x] `config/urls.py` - Integrated accounts URL configuration into root router.
- [x] `config/urls_public.py` - Updated canonical public URL allow-list per Architecture Spine AD-8.
- [x] `templates/accounts/auth_base.html` - Master split-pane shell with brand value propositions, pillar badges, and message alerts.
- [x] `templates/accounts/signup.html` - Registration page with real-time vanilla JS password strength meter and rule checks matching mockup `06-signup.html`.
- [x] `templates/accounts/verify_email.html` - OTP verification interface with 5-minute expiry alert and HTMX resend container matching mockup `07-verify-email.html`.
- [x] `templates/accounts/partials/resend_status.html` - HTMX partial for inline OTP resend updates without page reloads.
- [x] `templates/accounts/login.html` - Sign-in view with unverified user redirection matching mockup `08-login.html`.
- [x] `templates/accounts/welcome.html` - Full-bleed teal celebratory onboarding landing page matching mockup `11-welcome.html`.
- [x] `templates/accounts/password_reset.html` - Password reset request form matching mockup `09-forgot-password-request.html`.
- [x] `templates/accounts/password_reset_done.html` - Neutral confirmation notice preventing user enumeration.
- [x] `templates/accounts/password_reset_confirm.html` - Secure password entry form matching mockup `10-forgot-password-confirm.html`.
- [x] `templates/accounts/password_reset_complete.html` - Password change success confirmation page.
- [x] `templates/basha/partials/navbar.html` - Updated top navigation bar with dynamic session state (display name and logout form).

## Key Decisions
- **Session-Based Onboarding Continuity**: When a user registers or logs in with an unverified account, their user ID is stored in a temporary session key (`pending_verification_user_id`) to smoothly route them to `/accounts/verify-email/` without requiring them to re-enter email.
- **HTMX Resend Trigger**: The "Resend code" button uses HTMX to swap the status fragment in-place, showing remaining attempts and error states without disrupting user input.
- **Enumeration Protection**: The password reset submission displays the same confirmation screen regardless of whether the email exists in the database.

## Deviations from Plan
None. All planned views, forms, templates, and routes were implemented strictly according to specifications.

## Dependencies Added
None (uses native Django 5.2, HTMX 2.0.4, and Bootstrap 5.3 already installed).

## Developer Notes
- Ensure `config.settings.test` and `config.settings.dev` include `testserver` or localhost in `ALLOWED_HOSTS`.
- The logout route accepts both POST (preferred, with CSRF) and GET (convenience fallback redirecting to root).
