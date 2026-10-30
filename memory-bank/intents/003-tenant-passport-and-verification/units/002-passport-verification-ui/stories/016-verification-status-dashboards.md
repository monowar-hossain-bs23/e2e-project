---
id: 016-verification-status-dashboards
unit: 002-passport-verification-ui
intent: 003-tenant-passport-and-verification
status: ready
priority: must
created: '2026-10-30T13:40:00Z'
assigned_bolt: 006-passport-verification-ui
implemented: false
---

# Story: 016-verification-status-dashboards

## User Story

**As a** Basha Pass user,  
**I want** responsive dashboard views reflecting my current passport verification status (unverified, pending, rejected with countdown, or verified),  
**So that** I know exactly where my application stands and when I can take the next action.

## Acceptance Criteria

- [ ] **Given** an unverified tenant accessing the dashboard, **When** rendered, **Then** an unverified teaser card is displayed prompting them to verify their Tenant Passport (`docs/mockups/19-dashboard-unverified.html`).
- [ ] **Given** a tenant with a pending submission, **When** viewing the dashboard, **Then** an "In Review" status card is shown indicating typical review turnaround under 24 hours.
- [ ] **Given** a tenant whose submission was rejected, **When** viewing the dashboard, **Then** the rejection reason code, reviewer note, and a dynamic 24-hour countdown timer are displayed (`docs/mockups/21-dashboard-rejected.html`).
- [ ] **Given** a rejected tenant viewing the countdown, **When** the timer reaches zero, **Then** the resubmission CTA button becomes enabled automatically via HTMX polling or client script.
- [ ] **Given** a verified tenant, **When** viewing the dashboard, **Then** the verified trust badge and passport summary are rendered (`passport_header.html`, AD-5).

## Technical Notes

- Templates in `templates/passports/dashboards/`.
- Dynamic 24-hour countdown calculates remaining time using `last_rejection_at + 24 hours - now()`.
- Implements HTMX partial updates for status transitions.

## Dependencies

### Requires
- `013-verification-service-cooldown-and-audit`
- `015-passport-submission-wizard`

### Enables
- Full tenant onboarding lifecycle

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Tenant attempts to click resubmit before timer expires | Button is disabled; server enforces cooldown if forced |
| Rejection with no reviewer note | Card displays clean default explanation of canonical reason code |
| Verified user visiting rejection URL | Redirected to active dashboard |
