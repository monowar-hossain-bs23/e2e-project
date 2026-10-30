# System Architecture

## Overview
Basha Pass follows a modular monolith architecture built on Django MTV + HTMX partial-rendering with an explicit domain service layer. Views function strictly as thin HTTP adapters, delegating all domain logic, state mutations, and invariant enforcement to dedicated services.

## Architectural Style & Principles
- **Pattern**: Modular Monolith with explicit Service Layer (AD-1).
- **Presentation**: Server-rendered HTML with HTMX for dynamic partial updates and swaps (AD-5).
- **Data Access**: Django ORM with PostgreSQL, using standard UUID4 primary keys and normalized fields without external DB extensions.
- **Auditability**: Append-only audit logging (`AuditService`) executing within the same database transaction as domain mutations (AD-15).

## Bounded Contexts & Services

```text
URL → View (Thin HTTP Adapter) → Service (Business Rules & Mutations) → Template (Full or HTMX Partial)
                                      ↓
                             AuditService.append() (Same DB transaction)
```

### 1. Identity Context (`apps/accounts/`)
- **Entities**: Custom `User` model (tenant and admin). Admin role denoted by `is_staff=True` (AD-8).
- **Service**: `AccountService` handles authentication, 6-digit email OTP verification, and session flows.
- **Access Control**: Django standard session authentication; `LoginRequiredMixin` on authenticated CBVs; public allow-list in `config/urls_public.py`.

### 2. Verification Context (`apps/verification/`)
- **Entities**: Verification records, verification steps, and status history.
- **Service**: `VerificationService` is the **sole mutator** of passport state (`submitted`, `reviewing`, `verified`, `rejected`) and enforcer of:
  - Role-based transitions (tenant self-service vs. admin approval/rejection).
  - 24-hour resubmission cooldown enforcement (AD-2, FR-9).
  - Reject reason enum canonicalization (AD-4).
  - Transactional email dispatch on status transition (AD-7).
- **Storage**: `VerificationStorageService` is the sole reader/writer of private PII media (`private/` directory: NID front/back, selfies) with signed temporary URLs (AD-9).
- **Wizard**: 4-step wizard with step router (`step_next_for`) as the sole interpreter of user step navigation (AD-11).

### 3. Passport & Privacy Context (`apps/passports/`)
- **Entities**: `Passport`, `LifestyleProfile` (6 lifestyle axes: gender, occupation, smoking, sleep, area, budget).
- **Service**: `ConsentService` is the sole owner of what viewer X sees of passport Y or listing Z (AD-3). Produces immutable `Projection` objects, hiding contact info unless the viewer is verified.

### 4. Listing Context (`apps/listings/`)
- **Entities**: `Listing` (`kind ∈ {seat, room}`, `rent_bdt`, `rent_unit`, `rent_period=per_month`), `ListingPhoto` (1-7 photos).
- **Service**: `ListingService` enforces:
  - Active listing limit (≤3 active per author).
  - Verified-only creation requirement (FR-10).
  - Field locking post-publish (rent, body, photos editable; area, kind, unit locked).
  - Stale listing auto-archival (60 days) and withdrawal (AD-6).
- **Feed & Search**: `ListingFeedQuery` is the sole callable returning listings across the app (AD-12). Injects server-computed compatibility hints (0-6 matching lifestyle axes) and visibility projections.

### 5. Cross-Cutting Audit Context (`apps/audit/`)
- **Entities**: `AuditEntry` (append-only ledger).
- **Service**: `AuditService` records actor, action kind, target, before/after snapshots, and snapshot schema version in the same database transaction (AD-15).

## Component Structure & Source Tree
```text
config/
  settings/ (base.py, dev.py, prod.py, test.py)
  urls_public.py
  urls_authed.py
apps/
  accounts/
  verification/
  passports/
  listings/
  audit/
services/
  account/
  verification/
  consent/
  listing/
  audit/
templates/
  basha/
    partials/
static/
tests/
```

## Security & Privacy Invariants
- **Private PII Isolation**: Documents stored under `private/` MEDIA_ROOT, never directly accessible via public URL.
- **Stock Django Admin**: Admins use `django.contrib.admin`, authenticated via `is_staff=True`. Admin actions call domain services (e.g., `VerificationService.transition`) rather than writing ORM models directly (AD-10).
- **Result Envelope**: Services return explicit result envelopes `{ok: bool, value, errors: [...]}` for expected business rule violations, avoiding exception control flow for user validation (AD-6).
