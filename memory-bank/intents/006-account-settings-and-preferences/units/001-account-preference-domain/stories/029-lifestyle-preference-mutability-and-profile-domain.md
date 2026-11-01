---
story: 029-lifestyle-preference-mutability-and-profile-domain
unit: 001-account-preference-domain
intent: 006-account-settings-and-preferences
priority: Must
status: planned
created: '2026-11-01T11:45:00Z'
---

# Story 029: Lifestyle Preference Mutability & Profile Domain

## User Story

As a verified Basha Pass tenant or flat seeker,
I want to update my preferred Dhaka living areas and budget range in my lifestyle profile,
So that listing compatibility recommendations remain accurate as my living requirements change over time, without revoking my approved tenant verification.

## Acceptance Criteria

- [ ] **Decoupled Mutability Invariant**: `LifestyleProfile.clean()` permits updates to `area_preference`, `budget_min`, and `budget_max` even when `passport.is_verified` is True.
- [ ] **Core Lifestyle Protection**: Attempting to alter `gender`, `occupation`, `smoking`, or `sleep_schedule` on a verified passport raises `ValidationError` explaining that re-verification is required for core identity updates.
- [ ] **Area Validation**: `area_preference` must be a non-empty subset of the 13 canonical `DHAKA_SUB_AREAS`.
- [ ] **Budget Validation**: `budget_min` and `budget_max` must satisfy `500 <= budget_min <= budget_max <= 50000`.
- [ ] **Profile Service Mutation**: `AccountService.update_profile(user, display_name, phone_number)` validates handle length/regex and phone format, persists to `User`, and records an `AuditEntry` if the phone number changed.
- [ ] **Location Service Mutation**: `AccountService.update_location_preferences(user, areas, budget_min, budget_max)` validates and persists to `user.passport.lifestyle_profile`.

## Technical Notes

- Inspect `apps/passports/models.py::LifestyleProfile.clean()`. Currently, it blocks all saves on verified passports:
  ```python
  if current and current.passport.is_verified:
      raise ValidationError(...)
  ```
  Refine this condition to check if any core fields (`gender`, `occupation`, `smoking`, `sleep_schedule`) changed between `current` and `self`. If only `area_preference`, `budget_min`, `budget_max` changed, permit save!
- Add mutation helper methods on `AccountService` with clean transaction wrappers.

## Dependencies

- Depends on `apps.passports.models.LifestyleProfile` and `apps.accounts.services.account_service.AccountService`.
