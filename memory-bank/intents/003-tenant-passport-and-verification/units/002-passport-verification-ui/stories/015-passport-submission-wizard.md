---
id: 015-passport-submission-wizard
unit: 002-passport-verification-ui
intent: 003-tenant-passport-and-verification
status: complete
priority: must
created: '2026-10-30T13:40:00Z'
assigned_bolt: 006-passport-verification-ui
implemented: true
---

# Story: 015-passport-submission-wizard

## User Story

**As an** authenticated tenant,  
**I want** an intuitive, multi-step wizard to upload my NID documents and configure my lifestyle preferences,  
**So that** I can complete my verification application smoothly without confusion or data loss.

## Acceptance Criteria

- [ ] **Given** an authenticated user accessing `/passports/create/`, **When** the page loads, **Then** a multi-step form wizard is presented capturing display name, 6 lifestyle dimensions, and file upload for NID front, NID back, and selfie holding NID.
- [ ] **Given** file upload inputs, **When** files are selected, **Then** client-side and server-side validation enforces image types (JPEG, PNG, WebP) and maximum 5 MB file size with immediate visual feedback.
- [ ] **Given** the lifestyle preferences form, **When** fields are filled, **Then** the budget range slider is dynamically bounded between ৳500 and ৳50,000, and area preference supports multi-select across the 13 canonical Dhaka sub-areas.
- [ ] **Given** valid form submission, **When** processed, **Then** `VerificationService` records the submission in `submitted` state, redirects to the in-review dashboard, and shows a confirmation message.

## Technical Notes

- Views in `apps/passports/views.py` inheriting `LoginRequiredMixin`.
- Forms in `apps/passports/forms.py` using `LocaleFormMixin` (AD-13).
- Responsive layout styled in `static/css/passports.css` matching design tokens.

## Dependencies

### Requires
- `011-passport-and-lifestyle-models`
- `012-verification-model-and-private-storage`
- `013-verification-service-cooldown-and-audit`

### Enables
- `016-verification-status-dashboards`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User attempts to submit wizard without uploading selfie | Form validation error highlighting missing document |
| User already has a verified passport | Redirected to dashboard; cannot submit duplicate passport |
| User session expires during wizard | Form re-bind preserves valid text inputs (AD-13) |
