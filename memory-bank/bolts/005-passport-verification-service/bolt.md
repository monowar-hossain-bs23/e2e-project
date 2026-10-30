---
id: 005-passport-verification-service
unit: 001-passport-and-verification-domain
intent: 003-tenant-passport-and-verification
type: ddd-construction-bolt
status: in-progress
stories:
  - 011-passport-and-lifestyle-models
  - 012-verification-model-and-private-storage
  - 013-verification-service-cooldown-and-audit
  - 014-admin-verification-queue
created: '2026-10-30T13:40:00Z'
started: '2026-10-30T17:20:00Z'
completed: null
current_stage: design
stages_completed:
  - name: model
    completed: '2026-10-30T17:20:00Z'
    artifact: ddd-01-domain-model.md
requires_bolts:
  - 003-account-identity-service
enables_bolts:
  - 006-passport-verification-ui
requires_units:
  - 001-account-identity-service
blocks: false
complexity:
  avg_complexity: 3
  avg_uncertainty: 2
  max_dependencies: 2
  testing_scope: 2
---

# Bolt: 005-passport-verification-service

## Overview
Domain aggregate, services, private storage engine, and staff verification workflows for Basha Pass identity verification: `Passport` and `LifestyleProfile` models (6 lifestyle axes, post-verification immutability), `Verification` model with isolated private PII storage under `media_private/` (AD-9), staff-only authenticated document streaming view for admin previews, canonical 5-member reject reason enum (AD-4), `VerificationService` sole mutator state machine with 24-hour rejection cooldown (FR-9, AD-2), append-only `AuditEntry` transactional logging (AD-15), direct email dispatch within 5 minutes (FR-18), and Django Admin FIFO review queue (FR-7, AD-10).

## Objective
Establish the core trust foundation for Basha Pass, guaranteeing high-integrity identity verification, zero public PII exposure, spam/abuse mitigation via 24-hour cooldown, and durable auditability per PRD §4.2/§4.3, ERD §2/§3, and Architecture Spine AD-2, AD-4, AD-9, AD-10, AD-15.

## Stories Included
- **011-passport-and-lifestyle-models**: Passport & LifestyleProfile models, 6 dimensions, post-verify immutability (Must)
- **012-verification-model-and-private-storage**: Verification model, private PII storage under media_private/, 5-member canonical reject reasons enum (Must)
- **013-verification-service-cooldown-and-audit**: VerificationService sole mutator, 24h cooldown, AuditService append-only log, direct email dispatch (Must)
- **014-admin-verification-queue**: Django Admin FIFO verification review queue with high-res document previews, approve/reject/escalate actions (Must)

## Bolt Type
**Type**: DDD Construction Bolt
**Definition**: `.specsmd/aidlc/templates/construction/bolt-types/ddd-construction-bolt.md`

## Stages
- [x] **1. Model**: `ddd-01-domain-model.md`
- [ ] **2. Design**: `ddd-02-technical-design.md`
- [ ] **3. ADR**: Architecture decision record (e.g. private media storage & cooldown semantics)
- [ ] **4. Implement**: Source code in `apps/passports/`, `apps/verification/`, `apps/audit/`
- [ ] **5. Test**: Test suite in `tests/test_passports/`, `tests/test_verification/`, `tests/test_audit/` + `ddd-03-test-report.md`

## Dependencies

### Requires
- `003-account-identity-service` (Custom User model)

### Enables
- `006-passport-verification-ui`

## Success Criteria
- [ ] `Passport` and `LifestyleProfile` enforce 6 lifestyle dimensions and post-verification immutability
- [ ] NID front/back and selfie images saved exclusively to `media_private/` with zero public route exposure
- [ ] `VerificationService.transition(...)` enforces role authz, legal transitions, and 24-hour cooldown
- [ ] Direct email sent within 5 minutes of verification approval or rejection
- [ ] `AuditEntry` logged atomically for every verification state mutation
- [ ] Staff review queue in Django Admin orders submissions FIFO and requires canonical reason codes on rejection
- [ ] Automated pytest suite validates domain rules, transitions, cooldowns, and isolation
