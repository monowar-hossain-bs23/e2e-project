---
unit: 001-passport-and-verification-domain
intent: 003-tenant-passport-and-verification
phase: inception
status: complete
created: '2026-10-30T13:40:00Z'
updated: '2026-10-30T13:40:00Z'
unit_type: backend
default_bolt_type: ddd-construction-bolt
---

# Unit Brief: 001-passport-and-verification-domain

## Purpose

Deliver the foundational domain models, services, storage backends, and admin review workflows for Basha Pass Tenant Passports and verification lifecycle. Implements `Passport`, `LifestyleProfile`, `Verification`, and `AuditEntry` models; private PII storage under `media_private/` (AD-9); the `VerificationService` state machine (AD-2); canonical reject reasons enum (AD-4); 24-hour server-enforced rejection cooldown (FR-9); direct status email notifications (FR-18); and the FIFO admin review queue in Django Admin (FR-7, AD-10).

## Scope

### In Scope
- `Passport` and `LifestyleProfile` models with field validations, 13 canonical Dhaka areas, and post-verification immutability.
- `Verification` model tracking verification attempts, NID front/back paths, selfie path, state, reviewer, timestamps, and reason code.
- Private filesystem storage configuration (`media_private/`, AD-9) ensuring zero public access to NID and selfie images.
- Staff-only authenticated private media streaming view for Django admin previews.
- Canonical 5-member reject reason `Enum` in `apps/verification/services/reject_reasons.py` (AD-4).
- `VerificationService.transition(...)` as the sole mutator enforcing state transitions, role permissions, and the 24-hour cooldown.
- Append-only transactional audit logging in `AuditEntry` via `AuditService.append(...)` (AD-15).
- Direct status email dispatch via Django mail backend upon approval or rejection.
- Staff FIFO verification review queue in Django Admin with high-res document previews and approve/reject/escalate actions.

### Out of Scope
- Visitor/tenant-facing multi-step submission forms and dashboards (handled in Unit 2).
- Automatic OCR, face match, or external government eKYC APIs (deferred to v2 per PRD §4.3).

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Tenant Passport & Lifestyle Profile Foundation (Models & Rules) | Must |
| FR-2 | Private Identity Document Upload (Private Storage Backend) | Must |
| FR-3 | Verification State Machine & Service Isolation (`VerificationService`) | Must |
| FR-4 | Admin Verification Review Queue (FIFO & Staff Actions) | Must |
| FR-5 | Canonical Rejection Reasons & 24-Hour Cooldown (Backend Enforcement) | Must |
| FR-6 | Direct Status Email Notifications (Email Templates & Dispatch) | Must |
| FR-7 | Append-Only Audit Logging (`AuditEntry` & `AuditService`) | Must |

---

## Domain Concepts

### Key Entities
| Entity | Description | Attributes |
|--------|-------------|------------|
| `Passport` | The central credential proving identity verification | `id: UUIDv7/4`, `user_id: FK 1:1`, `display_name`, `status`, timestamps |
| `LifestyleProfile` | 6-axis compatibility preferences (1:1 with Passport) | `gender`, `occupation`, `smoking`, `sleep_schedule`, `area_preference`, `budget_min`, `budget_max` |
| `Verification` | A single verification attempt for a passport | `id: UUIDv7/4`, `passport_id: FK`, `state`, `nid_front_path`, `nid_back_path`, `selfie_path`, `reject_reason`, `last_rejection_at`, `reviewed_by`, `reviewed_at`, timestamps |
| `AuditEntry` | Immutable audit log entry | `actor_id`, `target_type`, `target_id`, `action`, `before_state`, `after_state`, `reason_code`, `timestamp` |

---

## Technical Constraints

- **Single Mutator (AD-2)**: `VerificationService` is the sole writer of verification states; views never mutate state directly.
- **Private Media Storage (AD-9)**: Document assets stored exclusively under `media_private/` using an isolated storage class; no public URL reverse resolution.
- **Transactional Audit (AD-15)**: State transition and audit logging executed within an atomic database transaction.
