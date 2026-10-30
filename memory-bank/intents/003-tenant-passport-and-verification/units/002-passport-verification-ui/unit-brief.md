---
unit: 002-passport-verification-ui
intent: 003-tenant-passport-and-verification
phase: inception
status: ready
created: '2026-10-30T13:40:00Z'
updated: '2026-10-30T13:40:00Z'
unit_type: frontend
default_bolt_type: simple-construction-bolt
---

# Unit Brief: 002-passport-verification-ui

## Purpose

Deliver the tenant-facing onboarding wizard, forms, and responsive status dashboards for Tenant Passport creation, identity document uploads, and verification tracking. Implements the unverified teaser dashboard (`19-dashboard-unverified.html`), multi-step submission wizard (`14-verify-step-1-phone.html`), in-review pending screen, dynamic 24-hour rejection countdown (`21-dashboard-rejected.html`), and verified passport header badge.

## Scope

### In Scope
- Tenant passport creation forms capturing display name and 6 lifestyle dimensions with client/server validation.
- Secure multipart file upload form for NID front, NID back, and selfie holding NID.
- Unverified tenant dashboard with verification CTA matching `docs/mockups/19-dashboard-unverified.html`.
- Verification in-review pending dashboard informing user of review SLA (<24 hours).
- Rejection dashboard displaying the rejection reason code, reviewer note, and a dynamic 24-hour countdown timer until resubmission is unlocked (`docs/mockups/21-dashboard-rejected.html`).
- Verified tenant passport badge (`passport_header.html`) unlocking listing creation.
- Responsive styling in `static/css/passports.css` matching Basha Pass brand tokens.
- Integration tests simulating visitor submission, validation failures, and dashboard states.

### Out of Scope
- Direct state machine mutations (delegated to `VerificationService`).
- Listing creation or feed browsing (handled in future listing intents).

---

## Assigned Requirements

| FR | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Tenant Passport & Lifestyle Profile Foundation (UI Form & Validation) | Must |
| FR-2 | Private Identity Document Upload (Multipart Upload Form UX) | Must |
| FR-5 | Canonical Rejection Reasons & 24-Hour Cooldown (UI Countdown Timer) | Must |
| FR-8 | Tenant Verification Wizards & Status Views (All Dashboards & Templates) | Must |

---

## Domain Concepts

### Presentation Surfaces
| Surface | Mockup Reference | Description |
|---------|------------------|-------------|
| Unverified Teaser | `19-dashboard-unverified.html` | Explains verification benefits and prompts passport submission |
| Passport Wizard | `14-verify-step-1-phone.html` / form | Captures display name, 6 lifestyle fields, and uploads 3 NID/selfie photos |
| In-Review State | Custom partial | Alerts tenant that documents are currently under staff review |
| Rejection Screen | `21-dashboard-rejected.html` | Displays reason code, note, and dynamic 24h countdown |
| Verified Header | `passport_header.html` (AD-5) | Surfaces verified trust badge and passport summary |
