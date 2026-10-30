---
id: 003-account-identity-service
unit: 001-account-identity-service
intent: 002-user-authentication-and-registration
type: ddd-construction-bolt
status: complete
stories:
  - 005-custom-user-model
  - 006-email-verification-token-and-service
  - 007-password-validation-and-auth-backend
created: '2026-10-30T10:07:00Z'
started: '2026-10-30T10:52:00Z'
completed: '2026-10-30T12:29:10Z'
current_stage: null
stages_completed:
  - name: model
    completed: '2026-10-30T10:53:00Z'
    artifact: ddd-01-domain-model.md
  - name: design
    completed: '2026-10-30T11:00:00Z'
    artifact: ddd-02-technical-design.md
  - name: adr
    completed: '2026-10-30T11:08:00Z'
    artifact: adr-001-hashed-email-otp-storage.md
  - name: implement
    completed: '2026-10-30T11:17:00Z'
    artifact: apps/accounts/
  - name: test
    completed: '2026-10-30T11:23:00Z'
    artifact: ddd-03-test-report.md
requires_bolts:
  - 001-core-foundation
enables_bolts:
  - 004-user-auth-ui
requires_units:
  - 001-core-foundation
blocks: false
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 1
  testing_scope: 2
---

# Bolt: 003-account-identity-service

## Overview
Domain aggregate and service layer for Basha Pass user identity: custom `User` model with UUID4 primary key, normalized case-insensitive email, `EmailVerificationToken` model with SHA-256 hashed storage, 5-minute expiry, `AccountService` logic, 5-rule password complexity validator, and transactional email dispatch.

## Objective
Establish the foundational Identity aggregate and service layer, ensuring secure user modeling, tamper-proof OTP handling, and session authentication capabilities per PRD §4.1, ERD §1, and Architecture Spine AD-8.

## Stories Included
- **005-custom-user-model**: Custom User model with UUID4 PK, case-insensitive email, and UserManager (Must)
- **006-email-verification-token-and-service**: EmailVerificationToken model (hashed OTP, 5m expiry), AccountService, and email dispatch (Must)
- **007-password-validation-and-auth-backend**: 5-rule password complexity validator, case-insensitive auth backend, 30-day session config (Must)

## Bolt Type
**Type**: DDD Construction Bolt
**Definition**: `.specsmd/aidlc/templates/construction/bolt-types/ddd-construction-bolt.md`

## Stages
- [ ] **1. Domain Model**: `ddd-01-domain-model.md`
- [ ] **2. Technical Design**: `ddd-02-technical-design.md`
- [ ] **3. ADR Analysis** (Optional): `adr-*.md`
- [ ] **4. Implement**: Source code in `apps/accounts/`
- [ ] **5. Test**: Tests in `tests/test_accounts/` + `ddd-03-test-report.md`

## Dependencies

### Requires
- `001-core-foundation`

### Enables
- `004-user-auth-ui`

## Success Criteria
- [ ] Custom `User` model configured as `AUTH_USER_MODEL` and migrated
- [ ] `AccountService` generates, hashes, and validates 6-digit OTP codes
- [ ] Tokens expire strictly after 5 minutes and single-use is enforced
- [ ] Resend attempts are capped at 3 per signup
- [ ] Password complexity validator enforces all 5 required rules
- [ ] Tests achieve >85% coverage across model, service, and validator
