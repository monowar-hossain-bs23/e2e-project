---
stage: plan
bolt: 006-passport-verification-ui
unit: 002-passport-verification-ui
intent: 003-tenant-passport-and-verification
created: '2026-10-31T00:51:00Z'
status: ready-for-review
---

# Implementation Plan: 002-passport-verification-ui

## Objective

Deliver the complete frontend presentation layer for tenant passport onboarding, document uploads, and verification status tracking. Build a multi-step submission wizard, unified dashboard dispatcher supporting all 4 tenant verification lifecycle states (unverified teaser, in-review pending, rejected with 24-hour countdown timer, and verified badge), and reusable passport trust badge header component, strictly adhering to design tokens and responsive mockups (`19-dashboard-unverified.html`, `21-dashboard-rejected.html`).

---

## Stories Included

- **015-passport-submission-wizard**: Multi-step wizard capturing display name, 6 lifestyle dimensions, and NID/selfie uploads (Must)
- **016-verification-status-dashboards**: Unverified teaser, in-review status, rejection screen with 24h countdown timer, and verified passport badge (Must)

---

## Deliverables

### 1. Forms & Validation (`apps/passports/forms.py`)
- `PassportSubmissionForm`: Multipart form capturing:
  - `display_name`: 3–32 chars, regex whitelist, uniqueness validation.
  - 6 lifestyle dimensions: `gender`, `occupation`, `smoking`, `sleep_schedule`, `area_preference` (multi-select subset of canonical 13 Dhaka areas), `budget_min`, `budget_max` (৳500–৳50,000 bounds).
  - Identity document uploads: `nid_front`, `nid_back`, `selfie` with client- and server-side file type (JPEG, PNG, WebP) and size (≤5MB) validation.
  - Integration with `LocaleFormMixin` (AD-13) for bilingual/localized field labels and error messages.

### 2. Views & Routing (`apps/passports/views.py`, `apps/passports/urls.py`, `config/urls.py`)
- `PassportWizardView` (`/passports/create/`):
  - Protected with `LoginRequiredMixin`.
  - Guard: Redirects to `/dashboard/` if user already has a `verified` passport or an active `pending` submission.
  - Guard: Checks 24-hour cooldown via `VerificationService.check_cooldown`. If cooldown active, redirects to `/dashboard/` with an advisory warning.
  - On submission: Creates/updates `Passport` and `LifestyleProfile`, calls `VerificationService.submit_verification(...)`, and redirects to `/dashboard/`.
- `DashboardView` (`/dashboard/`):
  - Protected with `LoginRequiredMixin`.
  - Inspects current passport and latest verification status:
    - **No passport / Unverified**: Renders unverified teaser dashboard (`_unverified_teaser.html`).
    - **Pending / In Review**: Renders under-review status card (`_in_review.html`, SLA <24h).
    - **Rejected**: Renders rejection view (`_rejected.html`) with canonical `reject_reason`, `reviewer_notes`, and remaining cooldown seconds.
    - **Verified**: Renders verified dashboard (`_verified.html`) featuring the verified passport badge.
- `DashboardStatusPartialView` (`/dashboard/status-partial/`):
  - Lightweight HTMX-polling endpoint returning the current status partial without a full-page reload when cooldown expires or staff transitions a submission.

### 3. Templates & Layouts (`templates/passports/`)
- `templates/passports/wizard.html`:
  - Visual 3-step progress bar (Step 1: Public Profile → Step 2: Lifestyle & Preferences → Step 3: Identity Verification Documents).
  - Client-side drag-and-drop file uploaders with real-time thumbnail previews and size checks.
- `templates/passports/dashboards/dashboard.html`:
  - Main responsive container extending `base.html`.
- `templates/passports/dashboards/_unverified_teaser.html`:
  - Matches mockup `19-dashboard-unverified.html` with verification benefits card and "Complete Passport" CTA.
- `templates/passports/dashboards/_in_review.html`:
  - Status card informing tenant that verification is underway with staff turnaround within 24 hours.
- `templates/passports/dashboards/_rejected.html`:
  - Matches mockup `21-dashboard-rejected.html`: displays canonical reason code, reviewer guidance, and interactive cooldown countdown.
- `templates/passports/dashboards/_verified.html`:
  - Verified tenant overview with lifestyle preferences and trust indicators.
- `templates/passports/partials/passport_header.html`:
  - Reusable component (AD-5) rendering verified badge `Verified Tenant`, handle, and lifestyle tag pills.

### 4. Styles & Interactive Scripts (`static/css/`, `static/js/`)
- `static/css/passports.css`:
  - Component styling for wizard step navigation, dropzone upload boxes, rejection alerts, and cooldown panels matching brand tokens (`--bp-primary: #0F6E7A`, `--bp-secondary: #C56B4F`, `--bp-warning-fg: #B45309`).
- `static/js/cooldown-timer.js`:
  - High-precision client-side countdown timer ticking down seconds; on expiry (`00:00:00`), automatically swaps the disabled button to an active "Resubmit Documents" CTA button via HTMX or DOM event.

---

## Dependencies

- **Bolt `004-user-auth-ui`**: Provides authenticated session context and `base.html` shell.
- **Bolt `005-passport-verification-service`**:
  - `apps.passports.models.Passport`, `LifestyleProfile`
  - `apps.verification.services.verification_service.VerificationService`
  - `apps.verification.services.storage.VerificationStorageService`
  - `apps.verification.services.reject_reasons.RejectReason`

---

## Technical Approach

```text
User Request
    │
    ▼
[DashboardView /dashboard/]
    ├── Unverified? ──────► Render _unverified_teaser.html (Mockup 19)
    ├── In Review?   ──────► Render _in_review.html
    ├── Rejected?   ──────► Check Cooldown ──► Render _rejected.html (Mockup 21) + Cooldown Timer
    └── Verified?   ──────► Render _verified.html + passport_header.html (AD-5)

[PassportWizardView /passports/create/]
    ├── Validate Inputs (Display Name, 6 Lifestyle Axes, 3 Document Files)
    ├── Atomic DB Transaction: Create/Update Passport & LifestyleProfile
    ├── Delegate to VerificationService.submit_verification()
    └── Redirect to /dashboard/
```

- **Separation of Concerns**: The presentation layer never touches verification state transitions or file filesystem directly; all operations delegate to `VerificationService` and `VerificationStorageService`.
- **Form Graceful Fallbacks**: Works seamlessly with vanilla POST and HTMX enhancement.
- **Strict Boundary Checks**: Enforces 24-hour cooldown server-side in `PassportWizardView` in addition to client-side button disabling.

---

## Acceptance Criteria

- [ ] **AC-1**: Authenticated user can navigate to `/passports/create/` and view the 3-step wizard with fields for display name, 6 lifestyle dimensions, and 3 file uploads.
- [ ] **AC-2**: Wizard rejects file uploads >5MB or unsupported formats (non-JPEG/PNG/WebP) with field errors.
- [ ] **AC-3**: Valid wizard submission creates a `Passport`, `LifestyleProfile`, and `Verification` record in `submitted` state, redirecting to `/dashboard/`.
- [ ] **AC-4**: Unverified user visiting `/dashboard/` sees the unverified teaser banner with benefits checklist per mockup `19`.
- [ ] **AC-5**: User with pending verification visiting `/dashboard/` sees the "In Review" status card with <24h SLA text.
- [ ] **AC-6**: User with rejected verification visiting `/dashboard/` sees the rejection reason, reviewer notes, and dynamic 24h countdown timer per mockup `21`.
- [ ] **AC-7**: When cooldown is active, the resubmission button is disabled; attempting to access `/passports/create/` redirects to `/dashboard/`.
- [ ] **AC-8**: Verified user visiting `/dashboard/` sees the verified trust badge (`passport_header.html`).
- [ ] **AC-9**: Automated test suite validates form validation, view permissions, dashboard state routing, and cooldown guarding with >90% coverage.
