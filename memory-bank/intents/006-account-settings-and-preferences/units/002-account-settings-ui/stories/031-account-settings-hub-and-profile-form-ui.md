---
story: 031-account-settings-hub-and-profile-form-ui
unit: 002-account-settings-ui
intent: 006-account-settings-and-preferences
priority: Must
status: complete
created: '2026-11-01T11:45:00Z'
completed: '2026-11-01T12:35:00Z'
---

# Story 031: Account Settings Hub & Profile Form UI

## User Story

As an authenticated Basha Pass tenant,
I want a dedicated Account Settings page accessible from the navigation menu to view my account status and update my profile handle and contact phone,
So that I can keep my personal identity and contact channels up to date.

## Acceptance Criteria

- [x] **Gated Settings View**: Accessing `/accounts/settings/` requires authentication; anonymous requests redirect to login.
- [x] **Navbar Integration**: Top navigation user dropdown includes an "Account Settings" item with a gear icon (`bi-gear`).
- [x] **Account Header Card**: Settings page displays user handle, registered email (read-only), join date, and passport verification badge (Verified, In Review, or Unverified).
- [x] **Profile Settings Form**: Form with `display_name` and `phone_number` fields, pre-populated with user's current data.
- [x] **Form Submission & Feedback**: Submitting valid profile updates persists changes, shows flash success message, and reflects immediately on the UI.
- [x] **Validation Feedback**: Invalid handle or malformed phone number displays inline error styling without page crashes.

## Technical Notes

- Form: `apps/accounts/forms.py::ProfileSettingsForm`.
- View: `apps/accounts/views.py::AccountSettingsView(LoginRequiredMixin, View)`.
- Route: Wire `/accounts/settings/` in `apps/accounts/urls.py` named `account_settings`.
- Template: `templates/accounts/settings.html`.
- Navbar: Update `templates/basha/partials/navbar.html`.

## Dependencies

- Depends on Story 029 (`AccountService.update_profile`).
