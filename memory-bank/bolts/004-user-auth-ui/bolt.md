---
id: 004-user-auth-ui
unit: 002-auth-ui-views
intent: 002-user-authentication-and-registration
type: simple-construction-bolt
status: complete
stories:
  - 008-signup-and-verify-email-views
  - 009-login-logout-and-session-views
  - 010-password-reset-views
created: '2026-10-30T10:07:00Z'
started: '2026-10-30T12:31:00Z'
completed: '2026-10-30T12:52:09Z'
current_stage: null
stages_completed:
  - name: plan
    completed: '2026-10-30T12:32:00Z'
    artifact: implementation-plan.md
  - name: implement
    completed: '2026-10-30T12:40:00Z'
    artifact: implementation-walkthrough.md
requires_bolts:
  - 001-core-foundation
  - 003-account-identity-service
enables_bolts: []
requires_units:
  - 001-account-identity-service
blocks: false
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 2
  testing_scope: 2
---

# Bolt: 004-user-auth-ui

## Overview
Presentation layer for Basha Pass authentication: visitor signup view, 6-digit email verification screen with HTMX resend trigger, login view with 30-day session cookies, authenticated logout endpoint, password reset views, welcome screen, and responsive templates matching approved design mockups (`06-signup`, `07-verify-email`, `08-login`, `09-forgot-password-request`, `10-confirm`, `11-welcome`).

## Objective
Provide an intuitive, responsive, and secure onboarding and authentication experience for tenants and staff, strictly aligned with Basha Pass brand tokens and Architecture Spine AD-8 public route allow-listing.

## Stories Included
- **008-signup-and-verify-email-views**: Signup view, verify email OTP interface, HTMX resend trigger, and welcome view (Must)
- **009-login-logout-and-session-views**: Login view with 30-day session persistence, logout endpoint, and unverified guards (Must)
- **010-password-reset-views**: Password reset request and confirmation views with token generation and reset email (Should)

## Bolt Type
**Type**: Simple Construction Bolt
**Definition**: `.specsmd/aidlc/templates/construction/bolt-types/simple-construction-bolt.md`

## Stages
- [ ] **1. Plan**: `implementation-plan.md`
- [ ] **2. Implement**: Source code + `implementation-walkthrough.md`
- [ ] **3. Test**: Test suite + `test-walkthrough.md`

## Dependencies

### Requires
- `001-core-foundation`
- `003-account-identity-service`

### Enables
- Future tenant passport wizard and listing creation flows

## Success Criteria
- [ ] Signup form validates display name, email, and password complexity
- [ ] OTP verification screen validates 6-digit code and logs in authenticated session
- [ ] HTMX resend button issues new code and enforces 3-attempt limit
- [ ] Login sets 30-day session cookie and handles unverified users gracefully
- [ ] Logout flushes session immediately
- [ ] Templates faithfully reproduce mockups with responsive desktop/mobile layouts
- [ ] Automated integration tests verify end-to-end view flows
