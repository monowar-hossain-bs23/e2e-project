---
intent: 002-user-authentication-and-registration
phase: inception
status: complete
created: '2026-10-30T09:24:00Z'
updated: '2026-10-30T10:47:00Z'
---

# Requirements: 002-user-authentication-and-registration

## Intent Overview

Provide secure, email-based authentication and account lifecycle management for Basha Pass tenants and administrators. This encompasses the custom User model foundation, user registration with password complexity enforcement, email verification via single-use 6-digit OTP tokens, persistent session login (30 days), logout, and password recovery, aligning strictly with PRD §4.1, ERD §1, and Architecture Spine AD-8.

## Business Goals

| Goal | Success Metric | Priority |
|------|----------------|----------|
| Frictionless tenant onboarding | Visitors can complete registration and email verification in under 2 minutes | Must |
| Account safety & spam prevention | Single-use 6-digit OTP with 5-minute expiry, SHA-256 hashed storage, and a strict 3-attempt resend limit | Must |
| Unified authentication spine | Single custom User model supporting tenants and staff, with session persistence (30 days) | Must |
| High-trust brand experience | Faithful responsive reproduction of auth mockups (`06-signup`, `07-verify-email`, `08-login`, `09-forgot-password`, `11-welcome`) | Must |

---

## Functional Requirements

### FR-1: Custom User Model & Accounts App Foundation
- **Description**: Implement custom `User` model (`apps.accounts.models.User`) inheriting `AbstractBaseUser` and `PermissionsMixin`, configured as `AUTH_USER_MODEL` in Django settings.
- **Acceptance Criteria**:
  - Primary key is standard UUID4 (`models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`).
  - Field `email`: `EmailField(unique=True, db_index=True)` with case-insensitive normalization on save.
  - Field `display_name`: `CharField(max_length=32, blank=False)`.
  - Flag `email_verified`: `BooleanField(default=False)` indicating verified email status.
  - Flags `is_staff`: `BooleanField(default=False)` and `is_active`: `BooleanField(default=True)`.
  - Timestamps `date_joined`, `last_login`, `created_at`, `updated_at`.
  - Custom `UserManager` implements `create_user(email, password, display_name=...)` and `create_superuser(email, password, ...)`.
  - `AUTH_USER_MODEL = 'accounts.User'` registered in `config/settings/base.py`.
  - Initial migration creates the table and tests verify user creation and case-insensitive email lookup.
- **Priority**: Must
- **Related Stories**: 005-custom-user-model

### FR-2: Email-based Visitor Signup & Password Complexity
- **Description**: Implement the public visitor signup page at `/accounts/signup/` taking email, display name, and password with robust validation rules.
- **Acceptance Criteria**:
  - Route registered in `config/urls_public.py` accessible without authentication.
  - Display name validation: 2 to 32 characters, regex `^[A-Za-z0-9 ._\-']+$`.
  - Email validation: standard RFC format; rejects existing email (case-insensitive).
  - Password complexity validator enforces all four classes:
    1. Minimum 8 characters
    2. At least one uppercase letter (`[A-Z]`)
    3. At least one lowercase letter (`[a-z]`)
    4. At least one number (`[0-9]`)
    5. At least one special symbol (`[!@#$%^&*(),.?":{}|<>]`)
  - Form displays inline error messages and visual password strength feedback.
  - On valid submission, unverified user is saved, verification OTP is issued, and user is redirected to `/accounts/verify-email/`.
- **Priority**: Must
- **Related Stories**: 006-signup-flow

### FR-3: 6-Digit Email Verification Token Generation & Dispatch
- **Description**: Model, generate, hash, and email 6-digit OTP verification tokens for new signups.
- **Acceptance Criteria**:
  - Model `EmailVerificationToken` (`apps.accounts.models.EmailVerificationToken`):
    - `id`: UUID4 PK
    - `user`: `ForeignKey(User, on_delete=CASCADE, related_name='verification_tokens')`
    - `token_hash`: `CharField(max_length=64)` storing SHA-256 hash of token (raw OTP never stored in DB)
    - `created_at`: `DateTimeField(auto_now_add=True)`
    - `expires_at`: `DateTimeField` (set to `created_at + 5 minutes`)
    - `consumed_at`: `DateTimeField(null=True, blank=True)`
    - `resend_count`: `PositiveSmallIntegerField(default=0)`
  - Token generator produces cryptographically secure 6-digit numeric string (`100000`–`999999`).
  - `AccountService.issue_verification_token(user)` creates the token record and sends email using Django transactional email.
  - Email uses HTML + text template displaying the 6-digit code and explicit 5-minute expiry notice.
- **Priority**: Must
- **Related Stories**: 007-email-verification-service

### FR-4: Token Verification & Account Activation Flow
- **Description**: Verification screen at `/accounts/verify-email/` where user inputs 6-digit code to verify their email address and activate their session.
- **Acceptance Criteria**:
  - Public route in `config/urls_public.py`.
  - Form accepts 6-digit OTP input.
  - `AccountService.verify_email_token(user, submitted_token)`:
    - Compares SHA-256 hash in constant time (`secrets.compare_digest`).
    - Validates token is not expired (`now() < expires_at`).
    - Validates token has not been consumed (`consumed_at is None`).
    - On valid token: sets `consumed_at = now()`, marks `user.email_verified = True`, persists changes.
    - Automatically authenticates user session via `django.contrib.auth.login(request, user)` and redirects to `/accounts/welcome/` (or passport setup).
  - Invalid code displays clear error ("Invalid verification code") without leaking token presence.
  - Expired token displays expiration error with one-click "Resend code" option.
  - Resend action:
    - Increments `resend_count`.
    - If `resend_count < 3`: generates new token, invalidates prior tokens, sends email.
    - If `resend_count >= 3`: rejects resend and prompts user to restart signup.
- **Priority**: Must
- **Related Stories**: 007-email-verification-service, 008-verify-email-ui

### FR-5: User Login with Session Persistence (30 Days)
- **Description**: Provide user login page at `/accounts/login/` supporting email and password authentication with 30-day session persistence.
- **Acceptance Criteria**:
  - Public route in `config/urls_public.py`.
  - Form takes email and password.
  - Authenticates via custom backend matching case-insensitive email.
  - Prevents login if account is disabled (`is_active=False`).
  - If user email is unverified, redirects to `/accounts/verify-email/` with alert to complete verification.
  - On valid credentials: creates authenticated session with 30-day cookie (`SESSION_COOKIE_AGE = 2592000`).
  - Redirects to `?next=` URL if safe, otherwise to tenant dashboard `/dashboard/` or welcome page.
- **Priority**: Must
- **Related Stories**: 009-login-and-logout

### FR-6: User Logout
- **Description**: Authenticated route at `/accounts/logout/` invalidating user session immediately.
- **Acceptance Criteria**:
  - Endpoint handles `POST` (with CSRF protection) and redirects to `/`.
  - Flushes session from store and expires session cookie on client.
  - Subsequent requests to protected routes redirect to `/accounts/login/`.
- **Priority**: Must
- **Related Stories**: 009-login-and-logout

### FR-7: Password Reset / Recovery Flow
- **Description**: Self-service password recovery flow for users who forget their password.
- **Acceptance Criteria**:
  - Request view at `/accounts/password-reset/` prompts for email.
  - Uses Django's secure `PasswordResetTokenGenerator` to dispatch email with secure link.
  - Confirm view at `/accounts/password-reset/confirm/<uidb64>/<token>/` prompts for new password.
  - Enforces the same 5-part password complexity rules as signup.
  - On successful reset, updates password hash, invalidates reset token, and redirects to login with success notice.
- **Priority**: Should
- **Related Stories**: 010-password-reset

### FR-8: Responsive Auth Templates & Design System Parity
- **Description**: Implement UI templates for auth views adhering strictly to brand design tokens (`#0F6E7A`, `#C56B4F`, `#FAFBFD`, typography, elevation) and layout patterns from mockups.
- **Acceptance Criteria**:
  - `templates/accounts/signup.html` matching `docs/mockups/06-signup.html` (2-column layout on desktop, stacked on mobile).
  - `templates/accounts/verify_email.html` matching `docs/mockups/07-verify-email.html` (OTP inputs, countdown visual, resend button).
  - `templates/accounts/login.html` matching `docs/mockups/08-login.html`.
  - `templates/accounts/welcome.html` matching `docs/mockups/11-welcome.html` (full-bleed teal background, welcome card, CTA to start verification).
  - Templates inherit from `templates/base.html` or dedicated `auth_base.html` sharing design tokens.
  - Fully accessible (WCAG AA compliant contrast, aria attributes, form labeling).
- **Priority**: Must
- **Related Stories**: 006-signup-flow, 008-verify-email-ui, 009-login-and-logout

---

## Non-Functional Requirements

### Performance
| Requirement | Metric | Target |
|-------------|--------|--------|
| Response Time | p95 latency for auth views | < 200ms |
| Password Hashing | PBKDF2 iterations / Argon2id memory-cost | Secure standard without blocking web worker (< 150ms per hash) |
| Database Indexing | Case-insensitive email lookup | Indexed column / unique index |

### Scalability
| Requirement | Metric | Target |
|-------------|--------|--------|
| Token Table | Automatic cleanup or indexed range | Supports 100K+ token rows with < 5ms lookup |
| Session Volume | Concurrent active sessions | 10,000+ active sessions |

### Security
| Requirement | Standard | Notes |
|-------------|----------|-------|
| Password Storage | PBKDF2 / Argon2id | Raw passwords never logged or stored |
| OTP Token Storage | SHA-256 hash | Raw OTP only in email, never in DB |
| OTP Brute Force | Expiry + 3-resend cap + rate limit | 5-minute validity window |
| Timing Attacks | `secrets.compare_digest` | Constant-time token verification |
| Session Security | `HttpOnly`, `SameSite=Lax`, `Secure` | Configured in Django settings |
| Route Protection | `LoginRequiredMixin` & `urls_public.py` | AD-8 public allow-list architecture |

### Reliability
| Requirement | Metric | Target |
|-------------|--------|--------|
| Email Delivery Abstraction | Development / Test safety | Local memory backend (`locmem`) in test/dev; SMTP in prod |
| Transaction Safety | DB Commit + Email dispatch | DB transaction commits before email dispatch (`transaction.on_commit`) |

---

## Constraints

### Technical Constraints
**Project-wide standards**:
- Python 3.12+, Django 5.2 LTS, Poetry, Ruff, pytest-django.
- Standard UUID4 primary keys and standard Django models (no custom PostgreSQL extensions required).
- Architectural Spine AD-1 (service layer under views), AD-8 (Django session auth, public allow-list in `config/urls_public.py`).

**Intent-specific constraints**:
- Email + password only in v1 (no SMS, no phone OTP, no social OAuth).
- Single custom User model (`accounts.User`) for both tenants and admin staff (`is_staff`).
- OTP tokens are 6 digits, 5-minute lifespan, single-use, max 3 resends.

### Business Constraints
- Launch city is Dhaka; initial language is English in v1.
- Gmail SMTP 500 emails/day ceiling is v1 design horizon.

---

## Assumptions

| Assumption | Risk if Invalid | Mitigation |
|------------|-----------------|------------|
| Standard Django UUID4 PKs provide sufficient uniqueness and safety | UUID collision risk (negligible) | Standard `uuid.uuid4` used universally across Django ecosystem |
| In-memory email backend for automated testing | Tests passing locally might fail on misconfigured prod SMTP | Integration tests mock SMTP backend cleanly; dev settings support console/env backend |
| 5-minute OTP expiry is optimal for urban Bangladesh connectivity | Users on slow connections experience expired tokens | 3 resend attempts allowed with instant new code generation |

---

## Open Questions

| Question | Owner | Due Date | Resolution |
|----------|-------|----------|------------|
| Should display name be globally unique or allow duplicates? | Inception | 2026-10-30 | Resolved: Non-unique in v1 (3-32 chars) as tenant identifier is email; display name is friendly handle (PRD FR-6) |
| Should unverified users be allowed to log in? | Inception | 2026-10-30 | Resolved: Unverified users who log in are redirected directly to `/accounts/verify-email/` to complete verification |
