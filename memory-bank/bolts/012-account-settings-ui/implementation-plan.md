---
stage: plan
bolt: 012-account-settings-ui
created: '2026-11-01T12:15:00Z'
---

# Implementation Plan: 012-account-settings-ui

## Objective

Deliver the complete, user-facing presentation and interaction layer for tenant account management. This encompasses the authenticated Account Settings hub view (`/accounts/settings/`), profile forms (`display_name`, `phone_number`), interactive Dhaka sub-area chip selector, budget range inputs, secure password rotation form with session preservation, flash messages, and top navigation bar integration.

---

## Deliverables

1. **Forms** (`apps/accounts/forms.py`):
   - `ProfileSettingsForm`: Handles `display_name` (2–32 chars, regex) and `phone_number` (sanitized Bangladeshi / E.164 format).
   - `LocationPreferencesForm`: Multi-select `area_preference` (from canonical 13 `DHAKA_SUB_AREAS`), `budget_min` (৳500+), `budget_max` (up to ৳50,000) with cross-field bounds validation.
   - `PasswordChangeForm`: Captures `current_password`, `new_password`, and `confirm_password` with password matching and complexity validation.

2. **View & Route** (`apps/accounts/views.py`, `apps/accounts/urls.py`):
   - `AccountSettingsView(LoginRequiredMixin, View)`:
     - Gated by `LoginRequiredMixin` with automatic redirect to login.
     - GET handler: Initialises and populates all 3 form cards with the user's current database state and eager passport/profile joins.
     - POST handler: Inspects form action submit buttons (`action="update_profile"`, `action="update_location"`, `action="change_password"`), executes domain mutations via `AccountService`, preserves active session via `update_session_auth_hash(request, user)` on password change, and dispatches Bootstrap alert flash messages.
   - Wired in `apps/accounts/urls.py` as `path("settings/", AccountSettingsView.as_view(), name="account_settings")`.

3. **Template & Visual Styling** (`templates/accounts/settings.html`, `static/css/account-settings.css`):
   - Responsive layout using platform design tokens (`var(--bp-canvas)`, `var(--bp-surface)`, `var(--bp-border)`).
   - Header summary banner showing avatar initial, display name, registered email (locked), verification status pill (`Verified`, `In Review`, `Unverified`), and account tenure.
   - Section 1: Profile Information card with public handle and contact phone inputs.
   - Section 2: Location & Search Preferences card with interactive Dhaka sub-area chips and monthly budget inputs (plus an informative CTA banner for users without a passport profile).
   - Section 3: Security & Credentials card with current password, new password, confirmation, and show/hide visibility toggles.

4. **Navigation Integration** (`templates/basha/partials/navbar.html`):
   - Adds "Account Settings" item with gear icon (`bi-gear`) into the authenticated user dropdown menu.

5. **Automated Integration Tests** (`tests/test_accounts/test_settings_views.py`):
   - Unauthenticated access redirects to `/login/?next=/accounts/settings/`.
   - GET populates current user profile and lifestyle preferences.
   - Successful profile update updates `User` and `Passport`.
   - Successful location preference update updates `LifestyleProfile` and immediately refreshes 6-axis compatibility scores on `/listings/`.
   - Password change succeeds and preserves active user session.

---

## Dependencies

- **Bolt 011** (`011-account-preference-domain`): Provides `AccountService.update_profile()`, `AccountService.update_location_preferences()`, `AccountService.change_password()`, and the decoupled mutability policy in `LifestyleProfile.clean()`.
- **Base Layout** (`templates/base.html`, `templates/basha/partials/navbar.html`): Shared header, navigation, and message alert partials.

---

## Technical Approach

- **Multi-Form Handling**: Use a clean single-view pattern with hidden or named submit inputs (`form_action` = `profile`, `location`, `password`). This keeps the URL canonical (`/accounts/settings/`) while giving granular field-level validation and error display for each independent card.
- **Session Preservation**: Use Django's built-in `django.contrib.auth.update_session_auth_hash(request, user)` immediately after password changes to prevent unexpected session logouts.
- **Dynamic Chip UI**: Use CSS toggle labels for Dhaka sub-areas matching the existing offcanvas filter drawer pattern (`.bp-chip` with hidden checkbox inputs).
- **Soft-Gated Protection**: Display a clear privacy note under the phone input explaining that contact information is soft-gated by `ConsentService` and visible strictly to verified seekers.

---

## Acceptance Criteria

- [ ] Unauthenticated visitor accessing `/accounts/settings/` is redirected to `/login/?next=/accounts/settings/`.
- [ ] Authenticated user dropdown in navbar links directly to `/accounts/settings/`.
- [ ] User can update display name and contact phone number, seeing instant feedback.
- [ ] User with a lifestyle profile can toggle Dhaka sub-areas and update budget range without model validation errors or verification loss.
- [ ] Updated location preferences immediately reflect on 6-axis compatibility dots in the `/listings/` feed.
- [ ] User can change their password with current password verification and 5-rule complexity validation without being logged out.
