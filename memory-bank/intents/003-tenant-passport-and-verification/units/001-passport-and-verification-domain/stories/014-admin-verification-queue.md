---
id: 014-admin-verification-queue
unit: 001-passport-and-verification-domain
intent: 003-tenant-passport-and-verification
status: complete
priority: must
created: '2026-10-30T13:40:00Z'
assigned_bolt: 005-passport-verification-service
implemented: true
---

# Story: 014-admin-verification-queue

## User Story

**As a** Basha Pass verification staff member,  
**I want** a dedicated FIFO review queue and document inspection interface in Django Admin,  
**So that** I can review pending tenant submissions in order of submission, inspect NID photos and selfies, and record approval or rejection with reason codes.

## Acceptance Criteria

- [ ] **Given** staff members navigating to Django Admin, **When** viewing the verification queue, **Then** pending submissions are sorted strictly FIFO by `submitted_at` (FR-7, AD-10).
- [ ] **Given** a submission opened for inspection, **When** viewed by staff, **Then** high-resolution previews of NID front, NID back, and selfie holding NID are displayed alongside user display name, submission timestamp, and lifestyle preferences.
- [ ] **Given** a pending submission, **When** staff clicks "Approve", **Then** `VerificationService.transition` is invoked to transition to `verified`, setting `reviewed_by` and `reviewed_at`.
- [ ] **Given** a pending submission, **When** staff clicks "Reject", **Then** staff must select one of the 5 canonical reason codes from the dropdown and may add an optional note before submitting.
- [ ] **Given** a complex or suspicious submission, **When** staff selects "Escalate", **Then** the record is flagged for secondary management review without finalizing approval or rejection.

## Technical Notes

- Implemented in `apps/verification/admin.py` using customized Django Admin changelist and changeform views.
- Media files are previewed via secure Django admin preview endpoints enforcing `is_staff=True`.
- Form actions delegate directly to `VerificationService.transition(...)` — admin view does not update models directly (AD-1, AD-2).

## Dependencies

### Requires
- `013-verification-service-cooldown-and-audit`

### Enables
- Operational staff review workflow
- `016-verification-status-dashboards`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Staff tries to reject without selecting reason code | Admin form validation error; reason code is mandatory |
| Two admins open the same submission simultaneously | Row lock / state check prevents duplicate transition or error |
| Non-staff user attempts to access admin review queue | Redirected to admin login or HTTP 403 |
