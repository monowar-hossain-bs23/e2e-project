---
id: 006-passport-verification-ui
unit: 002-passport-verification-ui
intent: 003-tenant-passport-and-verification
type: simple-construction-bolt
status: planned
stories:
  - 015-passport-submission-wizard
  - 016-verification-status-dashboards
created: '2026-10-30T13:40:00Z'
started: null
completed: null
current_stage: null
stages_completed: []
requires_bolts:
  - 004-user-auth-ui
  - 005-passport-verification-service
enables_bolts: []
requires_units:
  - 001-passport-and-verification-domain
blocks: false
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 2
  testing_scope: 2
---

# Bolt: 006-passport-verification-ui

## Overview
Presentation layer for tenant passport onboarding and verification tracking: multi-step passport submission wizard (capturing display name, 6 lifestyle preferences, and multipart NID/selfie photo uploads), unverified teaser dashboard (`19-dashboard-unverified.html`), in-review pending screen, dynamic 24-hour rejection countdown (`21-dashboard-rejected.html`), and verified passport badge (`passport_header.html`).

## Objective
Deliver an intuitive, responsive, and trustworthy onboarding experience for urban Dhaka renters to submit verification credentials and monitor their review status with real-time feedback and clear rejection guidance.

## Stories Included
- **015-passport-submission-wizard**: Multi-step wizard capturing display name, 6 lifestyle dimensions, and NID/selfie uploads (Must)
- **016-verification-status-dashboards**: Unverified teaser, in-review status, rejection screen with 24h countdown timer, and verified passport badge (Must)

## Bolt Type
**Type**: Simple Construction Bolt
**Definition**: `.specsmd/aidlc/templates/construction/bolt-types/simple-construction-bolt.md`

## Stages
- [ ] **1. Plan**: `implementation-plan.md`
- [ ] **2. Implement**: Source code + `implementation-walkthrough.md`
- [ ] **3. Test**: Test suite + `test-walkthrough.md`

## Dependencies

### Requires
- `004-user-auth-ui`
- `005-passport-verification-service`

### Enables
- Future listing creation and roommate matching intents

## Success Criteria
- [ ] Multi-step wizard captures display name, 6 lifestyle axes, and valid NID/selfie images
- [ ] Client-side and server-side validation enforces image constraints (JPEG, PNG, WebP ≤ 5MB)
- [ ] Unverified dashboard teaser prompts passport submission per mockup `19`
- [ ] In-review pending view alerts user to typical <24h review SLA
- [ ] Rejection view renders canonical reason code, reviewer note, and dynamic 24h countdown timer per mockup `21`
- [ ] Verified badge rendered in passport header per AD-5
- [ ] Automated integration tests verify end-to-end view flows
