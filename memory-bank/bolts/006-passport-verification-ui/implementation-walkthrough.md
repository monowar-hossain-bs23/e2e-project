---
stage: implement
bolt: 006-passport-verification-ui
unit: 002-passport-verification-ui
intent: 003-tenant-passport-and-verification
created: '2026-10-31T01:01:00Z'
status: complete
---

# Implementation Walkthrough: 002-passport-verification-ui

## Summary

Constructed the tenant-facing onboarding wizard, forms, and responsive verification status dashboards for Basha Pass. Implemented a 3-step passport submission wizard with client/server validation, a unified dashboard router supporting all four verification lifecycle states (unverified, pending, rejected with 24-hour cooldown, and verified), and a reusable verified tenant passport badge component.

## Structure Overview

The presentation layer is organized cleanly across `apps/passports/`, `apps/core/`, `templates/passports/`, and static assets:
- **Form Layer**: Validates display name, six lifestyle preference dimensions, and multipart identity image uploads, applying bilingual locale hints.
- **View Layer**: Protects endpoints with login authentication, enforces access guards (immutability, pending reviews, cooldowns), and delegates persistence and verification state mutations to domain services.
- **Presentation Layer**: Renders responsive UI components using Basha Pass design tokens, providing visual steppers, dropzones, status alert cards, and dynamic cooldown countdown timers.

## Completed Work

- [x] `apps/core/mixins.py` - Core `LocaleFormMixin` applying font stack styling and locale attributes to text-bearing form inputs.
- [x] `apps/passports/forms.py` - `PassportSubmissionForm` capturing public display name, six lifestyle axes, and identity documents with strict size and format validation.
- [x] `apps/passports/views.py` - `PassportWizardView`, `DashboardView`, and `DashboardStatusPartialView` governing onboarding flow and dynamic dashboard state routing.
- [x] `apps/passports/urls.py` - URL routing for passport creation and HTMX status polling endpoints.
- [x] `config/urls.py` - Mounted passport URLs and dedicated `/dashboard/` route.
- [x] `templates/passports/partials/passport_header.html` - Reusable verified badge, public handle, and lifestyle tag pills header component.
- [x] `templates/passports/dashboards/_unverified_teaser.html` - Unverified dashboard banner and benefits checklist card prompting verification.
- [x] `templates/passports/dashboards/_in_review.html` - Under-review status card detailing FIFO queue processing and turnaround SLA.
- [x] `templates/passports/dashboards/_rejected.html` - Rejection screen displaying reason codes, reviewer notes, and dynamic 24-hour countdown timer.
- [x] `templates/passports/dashboards/_verified.html` - Verified tenant dashboard showcasing verified badge and full platform access.
- [x] `templates/passports/dashboards/_status_container.html` - Dynamic container enabling HTMX partial swaps for status updates.
- [x] `templates/passports/dashboards/dashboard.html` - Main container dashboard layout integrating navigation, alerts, and status components.
- [x] `templates/passports/wizard.html` - Multi-step responsive wizard interface with step indicators, habit selectors, and file dropzones.
- [x] `static/css/passports.css` - Custom component styles for wizard steppers, dropzones, rejection panels, and verified badges.
- [x] `static/js/cooldown-timer.js` - High-precision client-side countdown timer managing real-time tick down and unlocking resubmission on expiry.

## Key Decisions

- **Separation of Concerns**: Presentation views and forms never mutate verification states or manipulate filesystem paths directly; all operations delegate to `VerificationService` and `VerificationStorageService`.
- **Pre-Population of Rejected Submissions**: When a user resubmits after rejection, existing non-PII lifestyle preferences and handles are preserved in form initial data, avoiding repetitive user entry.
- **Dual Cooldown Enforcement**: Cooldown is enforced both visually (disabled resubmit button and real-time JS countdown) and server-side in `PassportWizardView` and `VerificationService`.

## Deviations from Plan

None. All deliverables and components planned in `implementation-plan.md` have been fully constructed.

## Dependencies Added

None (built using vanilla Django, Bootstrap 5.3, and vanilla JavaScript).

## Developer Notes

- The `/dashboard/` view dynamically evaluates whether a user is unverified, pending review, rejected, or verified based on the user's latest passport and verification attempt.
- The `_status_container.html` fragment is equipped with an HTMX trigger to allow painless polling or event-based updates without requiring a full browser refresh.
