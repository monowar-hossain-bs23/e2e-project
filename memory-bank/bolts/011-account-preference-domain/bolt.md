---
id: 011-account-preference-domain
unit: 001-account-preference-domain
intent: 006-account-settings-and-preferences
type: ddd-construction-bolt
status: complete
stories:
  - 029-lifestyle-preference-mutability-and-profile-domain
  - 030-password-change-and-security-audit-service
created: '2026-11-01T11:46:00Z'
started: '2026-11-01T11:59:00Z'
completed: '2026-11-01T12:06:00Z'
current_stage: complete
stages_completed:
  - model
  - design
  - implement
  - test
requires_bolts:
  - 005-passport-verification-service
  - 009-listing-feed-query-and-consent
enables_bolts:
  - 012-account-settings-ui
requires_units: []
blocks: false
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 2
  testing_scope: 2
---

# Bolt: 011-account-preference-domain

## Overview

Core domain mutators and model validation refinements for tenant account profiles, living search parameters, and authentication credentials. Decouples search area preferences and monthly budget bounds from the post-verification immutability lock in `LifestyleProfile`, allowing living search parameters to update dynamically without revoking verification or triggering validation errors. Implements password verification, 5-rule password complexity checking, session hash updates, and append-only audit recording.

## Objective

Establish secure, tested mutation services and model invariants for account self-service (profile display name, contact phone, search areas, budget, and password) adhering to Architecture Spine AD-3, AD-7, and PRD §4.2, §4.4.

## Stories Included

- **029-lifestyle-preference-mutability-and-profile-domain**: `LifestyleProfile` mutability decoupling for search area/budget and profile domain mutations (Must)
- **030-password-change-and-security-audit-service**: In-app password rotation with complexity validation and append-only audit tracking (Must)

## Verification Plan

- Unit tests verifying `LifestyleProfile.clean()` permits updating `area_preference`, `budget_min`, `budget_max` on verified passports.
- Unit tests verifying `LifestyleProfile.clean()` still rejects mutations to `gender`, `occupation`, `smoking`, `sleep_schedule` on verified passports.
- Service tests for `AccountService.update_profile` validating display name regex and phone number formats.
- Service tests for `AccountService.change_password` testing bad current password, weak new password, valid update, and session auth hash maintenance.
- Audit tests asserting append-only `AuditEntry` records on phone number update and password rotation.
