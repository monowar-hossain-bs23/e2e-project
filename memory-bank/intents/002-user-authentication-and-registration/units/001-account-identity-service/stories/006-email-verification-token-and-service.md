---
id: 006-email-verification-token-and-service
unit: 001-account-identity-service
intent: 002-user-authentication-and-registration
status: complete
priority: must
created: '2026-10-30T10:06:00Z'
assigned_bolt: 003-account-identity-service
implemented: true
---

# Story: 006-email-verification-token-and-service

## User Story

**As a** new tenant signing up for Basha Pass  
**I want** to receive a 6-digit verification code via email and have it verified securely  
**So that** my email address is confirmed, spam accounts are prevented, and my account is safely activated  

## Acceptance Criteria

- [ ] **Given** a user account, **When** `AccountService.issue_verification_token(user)` is called, **Then** a cryptographically random 6-digit numeric OTP (`100000`–`999999`) is generated, stored hashed (SHA-256) in `EmailVerificationToken` with `expires_at = created_at + 5 minutes`, and emailed to the user via Django's email backend.
- [ ] **Given** an unconsumed token issued < 5 minutes ago, **When** `AccountService.verify_email_token(user, submitted_code)` is called with matching code, **Then** `consumed_at` is set, `user.email_verified = True`, and result returns `{ok: True, user: user}`.
- [ ] **Given** a token older than 5 minutes, **When** verification is attempted, **Then** the service rejects the token with `{ok: False, code: 'token_expired', message: 'Verification code has expired'}`.
- [ ] **Given** an invalid code, **When** verification is attempted, **Then** the service rejects with `{ok: False, code: 'token_invalid', message: 'Invalid verification code'}`.
- [ ] **Given** a user requesting resend, **When** `resend_count < 3`, **Then** prior unconsumed tokens are invalidated, a new OTP is issued, and `resend_count` is incremented.
- [ ] **Given** a user requesting resend, **When** `resend_count >= 3`, **Then** the service rejects with `{ok: False, code: 'resend_limit_exceeded', message: 'Maximum resend attempts reached. Please restart signup.'}`.

## Technical Notes

- Raw token is never stored in DB; only `hashlib.sha256(raw_token.encode()).hexdigest()` is stored in `token_hash`.
- Verification uses `secrets.compare_digest` to prevent timing attacks.
- Transactional email rendered from `templates/accounts/email/verify_email.html` (HTML + plain text fallback).

## Dependencies

### Requires
- `005-custom-user-model`

### Enables
- `008-signup-and-verify-email-views`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Re-using an already consumed token | Rejection with `token_invalid` |
| Token submitted after 5 mins 1 sec | Rejection with `token_expired` |
| 4th resend attempt | Rejection with `resend_limit_exceeded` |

## Out of Scope

- SMS delivery (email only in v1 per PRD §4.1)
