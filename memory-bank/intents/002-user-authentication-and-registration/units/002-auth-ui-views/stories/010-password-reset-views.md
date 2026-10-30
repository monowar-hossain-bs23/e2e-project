---
id: 010-password-reset-views
unit: 002-auth-ui-views
intent: 002-user-authentication-and-registration
status: complete
priority: should
created: '2026-10-30T10:06:00Z'
assigned_bolt: 004-user-auth-ui
implemented: true
---

# Story: 010-password-reset-views

## User Story

**As a** tenant who has forgotten their password  
**I want** to request a secure password reset link via email and reset my password  
**So that** I can recover access to my Basha Pass account safely  

## Acceptance Criteria

- [ ] **Given** a visitor accessing `GET /accounts/password-reset/`, **When** rendered, **Then** the page matches `docs/mockups/09-forgot-password-request.html`.
- [ ] **Given** submission of an email on `POST /accounts/password-reset/`, **When** processed, **Then** a secure one-time password reset link is generated using Django's `PasswordResetTokenGenerator` and emailed to the user, displaying a confirmation screen.
- [ ] **Given** a visitor submitting an unregistered email, **When** processed, **Then** the same confirmation screen is shown (preventing user enumeration).
- [ ] **Given** a visitor clicking the email reset link (`/accounts/password-reset/confirm/<uidb64>/<token>/`), **When** token is valid, **Then** the page matches `docs/mockups/10-forgot-password-confirm.html`.
- [ ] **Given** a valid new password meeting all 5 complexity rules, **When** submitted, **Then** the user's password is changed, prior reset tokens are invalidated, and user is redirected to login with a success notice.
- [ ] **Given** an invalid or expired reset link, **When** visited, **Then** the view displays an expired link notice with an option to request a new one.

## Technical Notes

- Leverages Django's built-in `PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`, `PasswordResetCompleteView` customized with Basha Pass templates and forms.
- Form inherits `PasswordComplexityValidator` to ensure all 5 password rules are maintained.

## Dependencies

### Requires
- `005-custom-user-model`
- `007-password-validation-and-auth-backend`

### Enables
- Self-service credential recovery

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Tampered or malformed `uidb64` or `token` | Safely handles without 500 error; shows invalid link message |
| Re-using an already consumed reset link | Rejection as invalid/expired |

## Out of Scope

- SMS-based reset codes
