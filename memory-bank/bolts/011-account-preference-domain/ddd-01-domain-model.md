---
unit: 001-account-preference-domain
bolt: 011-account-preference-domain
stage: model
status: complete
created: '2026-11-01T12:00:00Z'
---

# Static Model: 001-account-preference-domain

## Bounded Context

The **Account & Preference Domain** bridges the `Accounts` identity context and the `Passports` tenant lifestyle context. It governs user identity attributes (handle, contact phone), authentication credential rotation (password change), and tenant living search parameters (Dhaka sub-areas, budget bounds).

Crucially, it establishes the **Decoupled Search Mutability Invariant**: while core verified tenant identity attributes remain protected against tampering, living search parameters (`area_preference`, `budget_min`, `budget_max`) are decoupled and freely mutable by verified tenants to ensure dynamic compatibility matching on listing discovery surfaces without invalidating approved NID credentials.

---

## Domain Entities

| Entity | Properties | Business Rules |
|--------|------------|----------------|
| `User` (Aggregate Root) | `id: UUID4`<br/>`email: Email`<br/>`display_name: str`<br/>`phone_number: str \| None`<br/>`password: HashStr` | - `display_name`: 2–32 chars, regex `^[A-Za-z0-9 ._\-']+$`<br/>- `phone_number`: Validated Bangladeshi mobile (`01...`, `+8801...`, `8801...`) or E.164<br/>- `email`: Normalized, globally unique, read-only on profile update<br/>- `password`: Enforces 5-rule complexity (min 8 chars, uppercase, lowercase, digit, special symbol) |
| `Passport` (Aggregate Root) | `id: UUID7`<br/>`user: User`<br/>`status: StatusEnum`<br/>`display_name: str` | - OneToOne relationship with `User`<br/>- Governs tenant trust tier (`UNVERIFIED`, `IN_REVIEW`, `VERIFIED`, `REJECTED`)<br/>- Trust level determines contact disclosure eligibility via `ConsentService` |
| `LifestyleProfile` (Entity) | `id: UUID4`<br/>`passport: Passport`<br/>`gender: str`<br/>`occupation: str`<br/>`smoking: str`<br/>`sleep_schedule: str`<br/>`area_preference: list[str]`<br/>`budget_min: int`<br/>`budget_max: int` | - Core identity fields (`gender`, `occupation`, `smoking`, `sleep_schedule`) are **immutable** once `passport.is_verified = True`<br/>- Living search parameters (`area_preference`, `budget_min`, `budget_max`) are **mutable** regardless of verification status<br/>- `area_preference`: Must be non-empty subset of 13 canonical `DHAKA_SUB_AREAS`<br/>- `budget_min` / `budget_max`: `500 <= budget_min <= budget_max <= 50000` |

---

## Value Objects

| Value Object | Properties | Constraints |
|--------------|------------|-------------|
| `DhakaSubArea` | `name: str` | Must match one of 13 canonical sub-areas (`Mirpur`, `Dhanmondi`, `Gulshan`, `Banani`, `Uttara`, `Mohammadpur`, `Badda`, `Bashundhara`, `Khilkhet`, `Motijheel`, `Old Dhaka`, `Tejgaon`, `Baridhara`) |
| `BudgetRange` | `min_bdt: int`<br/>`max_bdt: int` | `500 <= min_bdt <= max_bdt <= 50,000` BDT per month |
| `PhoneNumber` | `value: str` | Sanitized phone string conforming to `^(\+?8801[3-9]\d{8}\|01[3-9]\d{8}\|\+?[1-9]\d{9,14})$` |
| `DisplayName` | `value: str` | Length 2 to 32 characters; character set restricted to `[A-Za-z0-9 ._\-']` |
| `RawPassword` | `value: str` | Ephemeral plaintext credential verified against current password hash or validated against 5 complexity rules |

---

## Aggregates

| Aggregate Root | Members | Invariants |
|----------------|---------|------------|
| `UserAggregate` (`User`) | `User`, `EmailVerificationToken` | - Primary email uniqueness across active users<br/>- Handle complexity and character set conformance<br/>- Password change requires authenticating current password and verifying 5 complexity rules<br/>- Session authentication hash must be updated concurrently on credential rotation |
| `PassportAggregate` (`Passport`) | `Passport`, `LifestyleProfile`, `Verification` | - Exactly one passport per user<br/>- If `is_verified` is true, alterations to core lifestyle dimensions (`gender`, `occupation`, `smoking`, `sleep_schedule`) are forbidden without re-verification submission<br/>- If `is_verified` is true, alterations to living search parameters (`area_preference`, `budget_min`, `budget_max`) are permitted and encouraged to keep recommendations accurate |

---

## Domain Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `ProfileUpdated` | User updates handle or contact phone number | `user_id: UUID`, `display_name: str`, `phone_number: str`, `timestamp: ISO8601` |
| `LocationPreferencesUpdated` | Tenant updates search areas or budget range | `user_id: UUID`, `passport_id: UUID`, `area_preference: list[str]`, `budget_min: int`, `budget_max: int`, `timestamp: ISO8601` |
| `PasswordChanged` | Tenant successfully rotates password | `user_id: UUID`, `timestamp: ISO8601` |
| `SecurityAuditRecorded` | Profile phone updated or password rotated | `actor_id: UUID`, `action: str`, `target_id: UUID`, `timestamp: ISO8601` |

---

## Domain Services

| Service | Operations | Dependencies |
|---------|------------|--------------|
| `AccountMutationService` (`AccountService`) | - `update_profile(user, display_name, phone_number)`<br/>- `update_location_preferences(user, areas, budget_min, budget_max)`<br/>- `change_password(user, current_password, new_password)` | `User`, `Passport`, `LifestyleProfile`, `AuditService`, `PasswordComplexityValidator` |
| `LifestyleImmutabilityPolicy` | - `validate_profile_mutation(current_profile, proposed_profile, is_verified)`: Rejects core identity mutations on verified profiles while permitting living search parameter updates | `LifestyleProfile`, `Passport` |

---

## Repository Interfaces

| Repository | Entity | Methods |
|------------|--------|---------|
| `UserRepository` | `User` | - `get_by_id(user_id: UUID) -> User`<br/>- `update_profile_fields(user: User, display_name: str, phone: str)`<br/>- `set_new_password(user: User, new_password: str)` |
| `LifestyleProfileRepository` | `LifestyleProfile` | - `get_for_user(user: User) -> LifestyleProfile \| None`<br/>- `update_search_preferences(profile: LifestyleProfile, areas: list[str], min_bdt: int, max_bdt: int)` |
| `AuditRepository` (`AuditService`) | `AuditEntry` | - `append(actor_id: UUID, target: Any, action: str, reason_code: str, after_state: dict)` |

---

## Ubiquitous Language

| Term | Definition |
|------|------------|
| **Living Search Parameters** | The subset of `LifestyleProfile` attributes (`area_preference`, `budget_min`, `budget_max`) representing where and at what price a seeker wishes to live. Intentionally decoupled from the verification lock to support self-service updates. |
| **Core Identity Dimensions** | The 4 foundational lifestyle attributes (`gender`, `occupation`, `smoking`, `sleep_schedule`) declared during passport submission and reviewed by admin verifiers. Strictly immutable post-verification. |
| **Decoupled Search Mutability** | Architectural invariant permitting verified tenants to update their living search parameters freely without invalidating their verification badge or triggering model validation errors. |
| **Canonical Dhaka Sub-Areas** | The 13 standardized geographic zones in Dhaka (`DHAKA_SUB_AREAS`) used across listing authoring, seeker preferences, and compatibility matching. |
| **Session Authentication Hash** | Django's HMAC token (`user.get_session_auth_hash()`) updated via `update_session_auth_hash` upon password rotation to prevent session termination while invalidating other stale sessions. |
