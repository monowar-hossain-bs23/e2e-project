---
story: 032-location-preference-and-password-change-ui
unit: 002-account-settings-ui
intent: 006-account-settings-and-preferences
priority: Must
status: complete
created: '2026-11-01T11:45:00Z'
completed: '2026-11-01T12:35:00Z'
---

# Story 032: Location Preference & Password Change UI

## User Story

As an authenticated tenant or seeker on Basha Pass,
I want to select my target Dhaka sub-areas, set monthly budget limits, and change my account password directly from the settings page,
So that my search matching preferences are refreshed and my credentials remain secure.

## Acceptance Criteria

- [x] **Location Preferences Form**: Form rendered with 13 canonical Dhaka sub-area interactive chips, `budget_min`, and `budget_max` inputs.
- [x] **Pre-Population**: When user has an existing `LifestyleProfile`, chips and budget fields are pre-populated with saved preferences.
- [x] **Unverified Seeker Support**: Users who haven't completed passport creation yet see an informative banner inviting them to complete Tenant Passport onboarding to unlock lifestyle matching.
- [x] **Password Change Form**: Form with `current_password`, `new_password`, and `confirm_password` inputs, with password show/hide toggle.
- [x] **Session Continuity**: Updating password calls `update_session_auth_hash(request, user)` so the user remains logged in.
- [x] **End-to-End Compatibility Refresh**: Updating location preferences immediately updates compatibility scores on the `/listings/` feed.

## Technical Notes

- Forms: `apps/accounts/forms.py::LocationPreferencesForm` and `apps/accounts/forms.py::PasswordChangeForm`.
- Handle multi-form submission on `AccountSettingsView` via distinct submit actions (`action="update_location"` and `action="change_password"`).
- Add JavaScript interaction for interactive chip toggles matching the design system in `filter_drawer.html`.

## Dependencies

- Depends on Story 029, Story 030, and Story 031.
