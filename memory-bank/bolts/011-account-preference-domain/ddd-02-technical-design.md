---
unit: 001-account-preference-domain
bolt: 011-account-preference-domain
stage: design
status: complete
created: '2026-11-01T12:02:00Z'
---

# Technical Design: 001-account-preference-domain

## Architecture Pattern

Following **Architecture Spine AD-6, AD-7, and AD-15**, this unit applies the **Service Layer Pattern** backed by DDD aggregate roots and model validation invariants.

- **Domain Model**: `LifestyleProfile.clean()` enforces entity invariants, distinguishing between strictly verified **Core Identity Dimensions** (`gender`, `occupation`, `smoking`, `sleep_schedule`) and self-service **Living Search Parameters** (`area_preference`, `budget_min`, `budget_max`).
- **Service Layer**: `AccountService` acts as the sole mutator for identity, living search preferences, and credential changes within atomic transaction blocks (`transaction.atomic`).
- **Audit Boundary**: Interacts with `AuditService.append` to record tamper-evident audit records on security-sensitive actions without leaking plaintext credentials.

---

## Layer Structure

```text
┌─────────────────────────────────────────────────────────────┐
│                 Presentation Layer (Unit 002)               │
│      AccountSettingsView, Forms, Chip Selectors, Navbar     │
├─────────────────────────────────────────────────────────────┤
│                 Application / Service Layer                 │
│                 AccountService (Sole Mutator)               │
│   • update_profile(user, display_name, phone_number)        │
│   • update_location_preferences(user, areas, min, max)      │
│   • change_password(user, current_password, new_password)   │
├─────────────────────────────────────────────────────────────┤
│                        Domain Layer                         │
│   • LifestyleProfile.clean() (Decoupled Mutability Policy)  │
│   • validate_dhaka_sub_areas, validate_budget_range         │
│   • validate_phone_number, PasswordComplexityValidator      │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure / Persistence                │
│   • Django ORM Models (User, Passport, LifestyleProfile)    │
│   • AuditService (Append-only AuditEntry ledger)            │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Contracts & Signatures

### 1. `AccountService.update_profile`
```python
@classmethod
def update_profile(
    cls,
    *,
    user: User,
    display_name: str,
    phone_number: str | None = None,
) -> dict[str, Any]:
    """Validate and update user public handle and contact phone.
    
    Returns:
        {'ok': True, 'user': User}
        or
        {'ok': False, 'code': str, 'message': str, 'errors': list[str]}
    """
```
- **Validation**:
  - `display_name`: 2–32 chars, regex `^[A-Za-z0-9 ._\-']+$`.
  - `phone_number`: Validated using `validate_phone_number()` if provided; permits `None` or blank.
- **Side Effects**:
  - Persists `user.save(update_fields=["display_name", "phone_number", "updated_at"])`.
  - If `phone_number` changed, appends an `AuditEntry`:
    `action="profile_updated"`, `reason_code="user_self_service"`, `after_state={"phone_number": phone_number}`.

---

### 2. `AccountService.update_location_preferences`
```python
@classmethod
def update_location_preferences(
    cls,
    *,
    user: User,
    area_preference: list[str],
    budget_min: int,
    budget_max: int,
) -> dict[str, Any]:
    """Validate and update tenant search areas and monthly budget limits.
    
    Returns:
        {'ok': True, 'profile': LifestyleProfile}
        or
        {'ok': False, 'code': str, 'message': str, 'errors': list[str]}
    """
```
- **Validation**:
  - Checks user has `passport` and `lifestyle_profile`.
  - `validate_dhaka_sub_areas(area_preference)`: non-empty list of canonical 13 Dhaka areas.
  - `validate_budget_range(budget_min, budget_max)`: `500 <= budget_min <= budget_max <= 50,000`.
- **Side Effects**:
  - Updates `profile.area_preference`, `profile.budget_min`, `profile.budget_max`.
  - Calls `profile.save(update_fields=["area_preference", "budget_min", "budget_max", "updated_at"])`.

---

### 3. `AccountService.change_password`
```python
@classmethod
def change_password(
    cls,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> dict[str, Any]:
    """Verify current password, validate complexity, and update password hash.
    
    Returns:
        {'ok': True, 'user': User}
        or
        {'ok': False, 'code': str, 'message': str, 'errors': list[str]}
    """
```
- **Validation**:
  - `user.check_password(current_password)` must be True; returns `code="invalid_current_password"` if false.
  - `PasswordComplexityValidator().validate(new_password)` must pass 5 complexity rules; returns `code="password_too_weak"` with message list if invalid.
- **Side Effects**:
  - `user.set_password(new_password)`.
  - `user.save(update_fields=["password", "updated_at"])`.
  - Appends `AuditEntry`: `action="password_changed"`, `reason_code="user_credential_rotation"`, `after_state={}` (zero plaintext password data).

---

### 4. `LifestyleProfile.clean()` Refinement
```python
def clean(self) -> None:
    super().clean()
    if self.budget_min is not None and self.budget_max is not None:
        validate_budget_range(self.budget_min, self.budget_max)
    if self.area_preference is not None:
        validate_dhaka_sub_areas(self.area_preference)

    # Immutability invariant: Core dimensions cannot be modified post-verification
    if self.pk:
        current = LifestyleProfile.objects.filter(pk=self.pk).first()
        if current and current.passport.is_verified:
            CORE_DIMENSIONS = ("gender", "occupation", "smoking", "sleep_schedule")
            for field in CORE_DIMENSIONS:
                if getattr(self, field) != getattr(current, field):
                    raise ValidationError(
                        _(
                            "Core lifestyle dimensions are immutable once passport is verified. "
                            "A new verification submission is required to update them."
                        )
                    )
```

---

## Data Persistence & Schema Plan

| Table | Operations | Migration Required? |
|-------|------------|---------------------|
| `accounts_user` | `display_name`, `phone_number`, `password`, `updated_at` | No (columns exist) |
| `passports_lifestyleprofile` | `area_preference` (JSON), `budget_min`, `budget_max`, `updated_at` | No (columns exist) |
| `audit_auditentry` | `actor_id`, `target_id`, `action`, `reason_code`, `after_state` | No (columns exist) |

---

## Security & Privacy Design

| Concern | Design Pattern |
|---------|----------------|
| **Current Password Verification** | Timing-attack resistant hash verification using `user.check_password()`. |
| **Password Hashing** | Standard Django PBKDF2 / Argon2 cryptographic hash with salt. |
| **No Credential Leakage** | `AuditService` state dictionaries explicitly omit password values. |
| **Session Continuity** | The presentation layer will invoke `update_session_auth_hash(request, user)` upon password change. |
| **PII Protection** | Contact phone number is soft-gated across all public-facing views via `ConsentService`. |

---

## Error Handling Matrix

| Error Condition | Error Code | HTTP / Form Impact |
|-----------------|------------|--------------------|
| Incorrect current password | `invalid_current_password` | Form error attached to `current_password` field |
| Weak new password | `password_too_weak` | Form error attached to `new_password` with unmet rule details |
| Non-canonical area in preference list | `invalid_dhaka_sub_area` | Form error attached to `area_preference` field |
| Inverted budget range (`min > max`) | `invalid_budget_range` | Form error attached to `budget_min` / `budget_max` |
| Attempt to mutate core verified dimension | `lifestyle_dimension_locked` | Model validation error preventing record save |
