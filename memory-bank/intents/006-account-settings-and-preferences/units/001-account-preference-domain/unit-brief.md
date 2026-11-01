---
unit: 001-account-preference-domain
unit_type: backend
default_bolt_type: ddd-construction-bolt
status: planned
created: '2026-11-01T11:44:00Z'
---

# Unit Brief: Account & Preference Domain

## Overview

The `001-account-preference-domain` unit implements the core business logic, model validation refinements, and mutation services for account management. Specifically, it refines `LifestyleProfile.clean()` to permit living search areas (`area_preference`) and monthly budget bounds (`budget_min`, `budget_max`) to be updated by verified tenants without revoking their approved verification credentials, while strictly preserving verification document immutability. It also implements password verification, complexity enforcement, and audit ledger append operations.

---

## Assigned Requirements

- **FR-2 (Domain)**: Validate `display_name` (2–32 chars, regex) and `phone_number` (BD / E.164 formats).
- **FR-3 (Domain)**: Decouple `area_preference` and budget range from verification lock; validate Dhaka sub-areas against canonical 13 list.
- **FR-4 (Domain)**: Verify current password against `check_password()`, enforce `PasswordComplexityValidator`, hash new password with `set_password()`, preserve session auth hash.
- **FR-5**: Append security audit records in `AuditService`.

---

## Domain Models & Entities

- `apps.accounts.models.User`: `display_name`, `phone_number`, password hashing.
- `apps.passports.models.LifestyleProfile`: `area_preference`, `budget_min`, `budget_max` mutability vs `gender`, `smoking`, `sleep_schedule` immutability when `passport.is_verified`.
- `apps.audit.models.AuditEntry`: `action="profile_updated"`, `action="password_changed"`.

---

## Key Operations

1. `LifestyleProfile.clean()`: Refined to check if core lifestyle dimensions (`gender`, `occupation`, `smoking`, `sleep_schedule`) changed on a verified passport. If only `area_preference`, `budget_min`, or `budget_max` changed, permit save.
2. `AccountService.update_profile(user, display_name, phone_number)`: Validates and updates user row, logs audit record if phone changed.
3. `AccountService.update_location_preferences(user, areas, budget_min, budget_max)`: Validates and updates user's `LifestyleProfile`.
4. `AccountService.change_password(user, current_password, new_password)`: Verifies current password, validates complexity, updates hash, logs audit record.

---

## Success Criteria & Test Boundaries

- Unit test verifying verified tenant CAN update `area_preference` and budget without error.
- Unit test verifying verified tenant CANNOT alter `gender`, `smoking`, or `sleep_schedule` directly without re-verification.
- Unit test verifying invalid phone numbers or bad Dhaka areas are rejected with clear ValidationError.
- Unit test verifying password update enforces 5 complexity rules and rejects incorrect current password.
