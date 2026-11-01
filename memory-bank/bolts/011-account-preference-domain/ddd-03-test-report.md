---
unit: 001-account-preference-domain
bolt: 011-account-preference-domain
stage: test
status: complete
updated: '2026-11-01T12:06:00Z'
---

# Test Report: 001-account-preference-domain

## Test Summary

| Category | Passed | Failed | Skipped | Status |
|----------|--------|--------|---------|--------|
| Unit (Model Invariants) | 8 | 0 | 0 | ✅ Pass |
| Integration (AccountService) | 18 | 0 | 0 | ✅ Pass |
| Security (Password & Audit) | 5 | 0 | 0 | ✅ Pass |
| Full Regression Suite | 282 | 0 | 0 | ✅ Pass (100%) |
| **Total** | **282** | **0** | **0** | ✅ **Pass (100%)** |

---

## Acceptance Criteria Validation

| Story | Acceptance Criteria | Status |
|-------|---------------------|--------|
| **029** | `LifestyleProfile.clean()` permits updating `area_preference`, `budget_min`, `budget_max` on verified passports | ✅ Pass |
| **029** | `LifestyleProfile.clean()` rejects altering core lifestyle dimensions (`gender`, `occupation`, `smoking`, `sleep_schedule`) on verified passports | ✅ Pass |
| **029** | `AccountService.update_profile` validates handle length & regex, phone format, and syncs handle to `Passport` | ✅ Pass |
| **029** | `AccountService.update_profile` logs `AuditEntry(action="profile_updated")` when phone number changes | ✅ Pass |
| **029** | `AccountService.update_location_preferences` validates canonical Dhaka areas & budget bounds and updates profile | ✅ Pass |
| **030** | `AccountService.change_password` verifies current password using `user.check_password()` | ✅ Pass |
| **030** | `AccountService.change_password` enforces 5 complexity rules via `PasswordComplexityValidator` | ✅ Pass |
| **030** | `AccountService.change_password` updates password hash and emits `AuditEntry(action="password_changed")` with zero plaintext passwords | ✅ Pass |

---

## Unit Tests

- `tests/test_passports/test_models.py::TestPassportModel::test_lifestyle_profile_immutability_on_verified_passport`:
  - Verified tenants can update living search parameters (`area_preference = ["Dhanmondi", "Mirpur"]`, `budget_max = 25000`) cleanly without validation error.
  - Verified tenants attempting to alter core dimensions (`smoking = YES`) receive `ValidationError("Core lifestyle dimensions are immutable once passport is verified")`.

---

## Integration Tests

- `tests/test_accounts/test_services.py::TestAccountService::test_update_profile_success_and_audits_phone_change`:
  - Updates `User.display_name` and `User.phone_number`.
  - Propagates display name update to `user.passport.display_name`.
  - Appends `AuditEntry` with `before_state` and `after_state`.
- `tests/test_accounts/test_services.py::TestAccountService::test_update_profile_invalid_display_name_fails`:
  - Enforces 2–32 char limit and regex format.
- `tests/test_accounts/test_services.py::TestAccountService::test_update_profile_invalid_phone_number_fails`:
  - Rejects non-phone strings and improper formats.
- `tests/test_accounts/test_services.py::TestAccountService::test_update_location_preferences_success`:
  - Updates `LifestyleProfile.area_preference` and budget range cleanly.
- `tests/test_accounts/test_services.py::TestAccountService::test_update_location_preferences_invalid_sub_area_fails`:
  - Rejects unknown areas outside the canonical 13.
- `tests/test_accounts/test_services.py::TestAccountService::test_update_location_preferences_inverted_budget_fails`:
  - Rejects budget min > budget max.
- `tests/test_accounts/test_services.py::TestAccountService::test_change_password_success_and_audits`:
  - Hashes new password, invalidates old password, and writes tamper-evident audit ledger record.
- `tests/test_accounts/test_services.py::TestAccountService::test_change_password_incorrect_current_fails`:
  - Blocks rotation when current password is wrong.
- `tests/test_accounts/test_services.py::TestAccountService::test_change_password_weak_new_password_fails`:
  - Blocks rotation when new password fails complexity rules.

---

## Performance & Regression Metrics

- **Execution Time**: Full test suite of 282 tests runs in **2.02 seconds**.
- **Regressions**: Zero regressions detected.
- **Code Quality**: `ruff check .` and `ruff format --check .` passed with 0 errors across 120 files.

---

## Ready for Bolt Completion

- [x] All acceptance criteria met for Stories 029 & 030
- [x] 100% test pass rate across 282 automated tests
- [x] Zero regressions introduced
- [x] Security audit trail verified
