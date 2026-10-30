---
intent: 002-user-authentication-and-registration
phase: inception
status: context-defined
created: '2026-10-30T09:24:00Z'
updated: '2026-10-30T10:02:00Z'
---

# 002-user-authentication-and-registration - System Context

## System Overview

The Identity Context provides the authentication, account creation, and credential verification backbone for Basha Pass. It establishes the custom User model (for both tenant and staff actors), implements public signup and login views, generates and verifies 6-digit email OTP tokens via Django SMTP, and enforces session persistence (30 days) and route protection via `LoginRequiredMixin` and `config/urls_public.py`.

## Actors

- **Visitor / Unregistered Seeker** (Human): Prospective tenant in Dhaka signing up with email, display name, and password.
- **Unverified Tenant** (Human): Newly registered user possessing an unconsumed 6-digit OTP verification token.
- **Verified Tenant** (Human): Active user with confirmed email who can log in and establish a 30-day persistent session.
- **Staff / Admin User** (Human): Basha Pass operator with `is_staff=True` authenticating via stock Django admin using the shared User model.
- **SMTP Gateway** (External System): Transactional email service (Gmail SMTP in prod, in-memory backend in dev/test) delivering OTP tokens.

## Boundaries & External Systems

- **Transactional Email Gateway**: Outbound SMTP delivery for 6-digit OTP codes and password reset links. Ceiling of 500 emails/day in v1.
- **Browser Client**: Renders HTML/HTMX forms, manages 30-day session cookies (`sessionid`), and evaluates client-side password strength rules.
- **PostgreSQL Database**: Persists `User` and `EmailVerificationToken` records with UUID4 primary keys and hashed tokens.
- **Verification & Passport Contexts (Downstream)**: Will consume `User` foreign keys to anchor tenant passports and listings.

## Data Flows

### Inbound
- **Signup Submission**: `email`, `display_name`, `password` via `POST /accounts/signup/`.
- **OTP Submission**: 6-digit code via `POST /accounts/verify-email/`.
- **Login Submission**: `email`, `password` via `POST /accounts/login/`.
- **Password Reset**: `email` via `POST /accounts/password-reset/`, new credentials via `POST /accounts/password-reset/confirm/<uidb64>/<token>/`.

### Outbound
- **Verification Email**: Transactional message with 6-digit OTP and 5-minute expiry alert.
- **Session Cookie**: Encrypted HTTP-only 30-day session cookie (`sessionid`).
- **Redirects**: Navigation flow to `/accounts/verify-email/`, `/accounts/welcome/`, or `/accounts/login/`.

## Context Diagram

```mermaid
graph TD
    Visitor["Visitor / Seeker"] -->|POST Signup (email, name, pwd)| AccountsApp["apps/accounts (Identity Context)"]
    AccountsApp -->|Issues 6-digit OTP| DB["PostgreSQL (User & EmailVerificationToken)"]
    AccountsApp -->|Sends transactional email| SMTP["Django SMTP Gateway"]
    SMTP -->|Delivers OTP code| Visitor
    Visitor -->|POST OTP Token| AccountsApp
    AccountsApp -->|Validates hash & consumes token| DB
    AccountsApp -->|Sets 30-day session| Visitor
    StaffUser["Staff / Admin"] -->|Authenticates (is_staff=True)| DjangoAdmin["Stock Django Admin (/admin/)"]
    DjangoAdmin -->|Queries User model| AccountsApp
```
