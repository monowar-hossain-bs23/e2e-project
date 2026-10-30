---
id: 011-passport-and-lifestyle-models
unit: 001-passport-and-verification-domain
intent: 003-tenant-passport-and-verification
status: ready
priority: must
created: '2026-10-30T13:40:00Z'
assigned_bolt: 005-passport-verification-service
implemented: false
---

# Story: 011-passport-and-lifestyle-models

## User Story

**As a** verified Basha Pass tenant,  
**I want** a persistent Tenant Passport and 6-dimension Lifestyle Profile linked to my account,  
**So that** I have a single, immutable identity profile that represents my rental preferences without exposing sensitive citizen data.

## Acceptance Criteria

- [ ] **Given** an authenticated user with verified email, **When** a `Passport` is created, **Then** it links 1:1 with `User` via UUID primary key, stores a unique display name (3–32 chars), and initializes status as `unverified`.
- [ ] **Given** a `Passport`, **When** its `LifestyleProfile` is populated, **Then** all 6 fields are strictly validated: `gender` (male, female, other), `occupation` (student, garments_worker, private_job, freelancer, other), `smoking` (yes, no, occasionally), `sleep_schedule` (early_bird, night_owl, flexible), `area_preference` (subset of 13 canonical Dhaka sub-areas), and `budget_min`/`budget_max` (৳500–৳50,000).
- [ ] **Given** a passport in `verified` status, **When** any update is attempted via UI or API on passport or lifestyle fields, **Then** the mutation is blocked by model/service immutability invariants (FR-3).

## Technical Notes

- Lives in `apps/passports/models.py`.
- Canonical 13 Dhaka sub-areas: Mirpur, Mohammadpur, Uttara, Banani, Gulshan, Baridhara, Bashundhara, Dhanmondi, Ramna, Tejgaon, Gazipur, Narayanganj-adjacent, Other.

## Dependencies

### Requires
- `005-custom-user-model` (Identity Context)

### Enables
- `012-verification-model-and-private-storage`
- `015-passport-submission-wizard`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Duplicate display name across passports | Rejection with validation error; display name must be unique |
| `budget_min` exceeds `budget_max` | Validation error: minimum budget cannot exceed maximum |
| Verified user attempts to edit lifestyle profile | Blocked; re-verification required to modify verified details |
