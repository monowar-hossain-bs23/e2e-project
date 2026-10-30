---
intent: 003-tenant-passport-and-verification
phase: inception
status: complete
created: '2026-10-30T13:00:00Z'
updated: '2026-10-30T13:40:00Z'
---

# Requirements: 003-tenant-passport-and-verification

## Intent Overview

Provide verified tenant identity and lifecycle management for Basha Pass through the **Tenant Passport** and manual **Verification Process**. This establishes a portable, privacy-preserving credential for urban Dhaka renters, replacing repeated offline NID submissions.

This intent encompasses:
1. Creation of `Passport` and `LifestyleProfile` models with 6 lifestyle dimensions, public display name handle, and strict post-verification immutability (FR-3, FR-4, FR-6).
2. Secure private document upload for NID front, NID back, and selfie holding NID, stored under `media_private/` (AD-9).
3. The verification state machine (`submitted` → `reviewing` → `verified` / `rejected`) strictly controlled by `VerificationService` (AD-2).
4. Staff review queue with FIFO ordering, review screen, approval, escalation, and rejection with 5 canonical reason codes (FR-7, FR-8, AD-4, AD-10).
5. Server-enforced 24-hour cooldown before a rejected passport can be resubmitted (FR-9).
6. Transactional append-only audit trail logging in `AuditEntry` (AD-15) and direct email status delivery (FR-18, AD-7).
7. Tenant-facing status dashboards and submission wizard interfaces matching mockups `14-verify-step-1-phone.html`, `19-dashboard-unverified.html`, and `21-dashboard-rejected.html`.

## Business Goals

| Goal | Success Metric | Priority |
|------|----------------|----------|
| Single portable verification | Verified tenants verify their identity once and carry an immutable Tenant Passport across rental contexts | Must |
| Trust & scam elimination | 100% of listers and contact-seekers are verified by staff against NID front/back + selfie | Must |
| PII privacy preservation | NID photos, selfie, and real name are never exposed to other tenants; visible only to authenticated staff | Must |
| Fast SLA & clear feedback | Verification queue processed FIFO; email status sent within 5 minutes of review; clear rejection reason code | Must |
| Queue flood prevention | 24-hour server-side cooldown on rejected passports prevents spam and rapid resubmission abuse | Must |

---

## Functional Requirements

### FR-1: Tenant Passport & Lifestyle Profile Foundation
- **Description**: Authenticated users with verified email accounts can create a single `Passport` object associated with their `User` record, including their public display name and a 1:1 `LifestyleProfile` record.
- **Acceptance Criteria**:
  - `Passport` model has `id` (UUIDv7/UUID4 PK), `user_id` (`1:1` with User, `ON DELETE CASCADE`), `display_name` (3–32 chars, regex `^[A-Za-z0-9 ._\-']+$`), `status` (`unverified`, `pending`, `verified`, `rejected`), and timestamps.
  - `LifestyleProfile` model has `passport_id` (`1:1` with Passport, `ON DELETE CASCADE`), `gender` (`male`, `female`, `other`), `occupation` (`student`, `garments_worker`, `private_job`, `freelancer`, `other`), `smoking` (`yes`, `no`, `occasionally`), `sleep_schedule` (`early_bird`, `night_owl`, `flexible`), `area_preference` (JSON list of 13 canonical Dhaka sub-areas), and `budget_min`/`budget_max` (integers ৳500–৳50,000).
  - All 6 lifestyle fields and display name are mandatory before passport submission.
  - **Immutability rule (FR-3)**: Once verified, passport and lifestyle profile fields cannot be modified via UI or API. Changing verified data requires starting a fresh verification submission.
- **Priority**: Must
- **Related Stories**: TBD

### FR-2: Private Identity Document Upload (NID & Selfie)
- **Description**: Provide private file upload handling for NID front, NID back, and a selfie holding the NID as part of a verification attempt.
- **Acceptance Criteria**:
  - Accepts image formats: JPEG, PNG, and WebP with a maximum size limit of 5 MB per file.
  - Stored strictly in private media storage (`media_private/` directory, per Architecture Spine AD-9).
  - Files are never accessible via Django's public media static URLs or unauthenticated HTTP requests.
  - Files are served only through authenticated staff views enforcing `is_staff=True` permissions.
- **Priority**: Must
- **Related Stories**: TBD

### FR-3: Verification State Machine & Service Isolation
- **Description**: Implement `apps/verification/services/verification_service.py` (`VerificationService`) as the sole mutator of passport verification state, enforcing role-based permissions, state legality, and prerequisites (Architecture Spine AD-2).
- **Acceptance Criteria**:
  - State machine transitions: `submitted` → `reviewing` → `verified` or `rejected`.
  - Self-service transitions (`submit`, `resubmit`) are authorized only for the passport owner.
  - Review transitions (`reviewing`, `verified`, `rejected`, `escalate`) are authorized only for authenticated staff (`user.is_staff=True`).
  - Attempting an illegal transition returns `{ok: false, code: "invalid_transition"}`.
  - Attempting an unauthorized transition returns `{ok: false, code: "forbidden_role"}`.
  - Transitioning to `verified` marks `Passport.status = 'verified'` and `User.email_verified = True`.
- **Priority**: Must
- **Related Stories**: TBD

### FR-4: Admin Verification Review Queue
- **Description**: Provide an admin review queue and inspection interface for internal staff to examine pending verification submissions (PRD §4.3 FR-7, AD-10).
- **Acceptance Criteria**:
  - Queue lists all pending submissions sorted FIFO by `submitted_at`.
  - Opening a submission for review transitions state to `reviewing` (internal state).
  - Dedicated review screen displays NID front, NID back, selfie, user display name, submission timestamp, and lifestyle summary.
  - Staff can **Approve** (transitions to `verified`, sets `reviewed_by` and `reviewed_at`).
  - Staff can **Reject** (transitions to `rejected`, requires a mandatory reason code and optional note, records `last_rejection_at`).
  - Staff can **Escalate** (flags submission for secondary manager review).
- **Priority**: Must
- **Related Stories**: TBD

### FR-5: Canonical Rejection Reasons & 24-Hour Cooldown
- **Description**: Enforce fixed canonical reason codes for rejections and a strict 24-hour server-side cooldown before resubmission (PRD §4.3 FR-8, FR-9, AD-4).
- **Acceptance Criteria**:
  - Rejection requires selecting from a 5-member Python `Enum` (`apps/verification/services/reject_reasons.py`): `expired`, `mismatch`, `illegible`, `tampering_suspected`, `other`.
  - Rejection sets `last_rejection_at` timestamp on the `Verification` record.
  - Resubmission within 24 hours of rejection is blocked at the service level with `{ok: false, code: "cooldown_active", remaining_seconds: ...}`.
  - After 24 hours elapse, the tenant may submit a fresh verification attempt; prior NID photos are never reused (FR-3).
- **Priority**: Must
- **Related Stories**: TBD

### FR-6: Direct Status Email Notifications
- **Description**: Send immediate automated email notifications to the tenant upon verification approval or rejection (PRD §4.7 FR-18, AD-7).
- **Acceptance Criteria**:
  - `VerificationService` directly triggers email dispatch via Django's mail system upon state transition.
  - Approval email confirms passport verification and provides a CTA to view dashboard or create listings.
  - Rejection email clearly explains the human-readable reason for rejection and explicitly states the 24-hour cooldown period before resubmission.
  - Email notification is dispatched within 5 minutes of the review decision.
- **Priority**: Must
- **Related Stories**: TBD

### FR-7: Append-Only Audit Logging
- **Description**: Record an immutable `AuditEntry` in the same database transaction for every verification state transition (Architecture Spine AD-15).
- **Acceptance Criteria**:
  - `AuditService.append(...)` records: `actor_id` (admin user or tenant), `target_type: "verification.Verification"`, `target_id: UUID`, `action: "transition"`, `before_state`, `after_state`, `reason_code` (if rejected), and timestamp.
  - Audit rows are append-only and cannot be updated or deleted.
- **Priority**: Must
- **Related Stories**: TBD

### FR-8: Tenant Verification Wizards & Status Views
- **Description**: User-facing views and responsive templates guiding the tenant through passport creation, submission, and status monitoring.
- **Acceptance Criteria**:
  - **Unverified Teaser**: Unverified dashboard showing "Verify your passport" prompt (`19-dashboard-unverified.html`).
  - **Submission Wizard / Form**: Form capturing display name, 6 lifestyle dimensions, and file upload for NID front, NID back, and selfie (`14-verify-step-1-phone.html` / verification form).
  - **Pending State View**: Informs tenant that submission is in review (usually under 24 hours).
  - **Rejected State View**: Informs tenant of rejection reason, reviewer note, and dynamic 24h countdown timer until resubmission is unlocked (`21-dashboard-rejected.html`).
  - **Verified State View**: Renders verified passport header badge and unlocks listing creation.
- **Priority**: Must
- **Related Stories**: TBD

---

## Non-Functional Requirements

### Performance
| Requirement | Metric | Target |
|-------------|--------|--------|
| Queue List Latency | p95 query response time | < 150ms for pending queue (indexed on `state`, `submitted_at`) |
| Image Upload | File size processing | Max 5 MB per photo; upload processed and stored in < 1.5s |
| Email SLA | Dispatch time | Status notification email dispatched in < 5 minutes (near-instantaneous in Celery/sync) |

### Scalability
| Requirement | Metric | Target |
|-------------|--------|--------|
| Verification Queue Throughput | Review queue capacity | Capable of handling 500+ submissions/day with FIFO ordering |
| Media Storage Growth | Storage volume | Isolated private directory structure scaling gracefully with UUID-named assets |

### Security & Privacy
| Requirement | Standard | Notes |
|-------------|----------|-------|
| PII Storage Isolation | AD-9 Private Media Storage | NID and selfie photos stored under `media_private/`; inaccessible via public URLs |
| Access Control (RBAC) | AD-2 & AD-10 | Staff-only access to pending queue and raw PII media; enforced via `is_staff` check |
| Tenant Privacy | AD-3 ConsentService | NID photos, selfie, and citizen ID numbers are NEVER projected to other tenants |
| Anti-Enumeration & ID Security | UUIDv7 / UUID4 PKs | All models (`Passport`, `Verification`, `LifestyleProfile`) use UUID primary keys |

### Reliability & Consistency
| Requirement | Metric | Target |
|-------------|--------|--------|
| Transactional Integrity | Atomic state transition | State update, passport status, and `AuditEntry` recorded in a single `transaction.atomic()` |
| Re-submission Cooldown | Server-enforced 24h | Cooldown calculated via `timezone.now() - last_rejection_at >= 24h`; client cannot bypass |

### Compliance & Standards
| Requirement | Standard | Notes |
|-------------|----------|-------|
| Architecture Spine Alignment | AD-1, AD-2, AD-3, AD-4, AD-7, AD-9, AD-10, AD-15 | Strict adherence to bounded contexts, single mutator, enum reason codes, and audit trail |
| Code Standards | Ruff linting & formatting | 100% compliance with 88-char formatting and zero lint errors |

---

## Constraints

### Technical Constraints
- **Private File Storage**: Django's default `MEDIA_ROOT` serves public assets. Private documents require a distinct `FileSystemStorage` pointing to `media_private/` with no direct URL routing.
- **Single Mutator**: Views must never mutate verification state directly; all status changes must flow through `VerificationService.transition(...)`.
- **v1 Manual Scope**: Automated OCR, biometric face match, and government eKYC APIs are strictly out of scope for v1 (deferred to v2 per PRD §4.3).

### Business Constraints
- **Immutable Passports**: In v1, verified passports cannot be edited to eliminate fraud (no swapping identity or rewriting lifestyle profiles post-verification).
- **Single Active Passport**: Each registered user may have at most one active Tenant Passport.

---

## Assumptions

| Assumption | Risk if Invalid | Mitigation |
|------------|-----------------|------------|
| 1. Staff volume can handle manual verification in v1 (<500/day) | Queue backlog exceeding 24 hours | FIFO ordering, clear reason codes, and escalate state to prioritize workloads |
| 2. Private filesystem storage is sufficient for single-server v1 | Storage migration needed for multi-server cloud deployment | Storage backend wrapped behind an abstract interface (`VerificationStorageService`) |
| 3. Tenants have access to NID front/back and selfie | Drop-off during onboarding wizard | Clear helper text, file size warnings, and unverified state dashboard explaining value proposition |

---

## Open Questions

| Question | Owner | Due Date | Resolution |
|----------|-------|----------|------------|
| 1. Dynamic budget slider floor/ceiling | Product | Inception | Seeded with ৳500 floor and ৳50,000 ceiling per PRD §4.2 |
| 2. Canonical Dhaka sub-areas | Product | Inception | Fixed 13 areas: Mirpur, Mohammadpur, Uttara, Banani, Gulshan, Baridhara, Bashundhara, Dhanmondi, Ramna, Tejgaon, Gazipur, Narayanganj-adjacent, Other |
