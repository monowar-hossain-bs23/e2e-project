---
unit: 002-account-settings-ui
unit_type: frontend
default_bolt_type: simple-construction-bolt
status: complete
created: '2026-11-01T11:44:00Z'
---

# Unit Brief: Account Settings UI

## Overview

The `002-account-settings-ui` unit delivers the user-facing Account Settings hub view (`/accounts/settings/`), forms, interactive area selection chips, security forms, feedback alerts, and navigation links. It enables tenants to effortlessly inspect and update their profile details, adjust living search areas with visual feedback, change passwords, and navigate back to their dashboard or listings.

---

## Assigned Requirements

- **FR-1**: Authenticated Account Settings hub page with tabbed/card organization, verification badge, and email display.
- **FR-2 (UI)**: Profile settings form component with display name and phone number fields.
- **FR-3 (UI)**: Location preferences form component with 13 Dhaka sub-area interactive chips and budget range inputs.
- **FR-4 (UI)**: Password change form component with current and new password fields, password toggle visibility, and error states.
- **FR-1 (Nav)**: Wire settings link in the top navigation user dropdown menu.

---

## Key Components & Templates

1. `apps/accounts/forms.py`:
   - `ProfileSettingsForm`: Handles `display_name` and `phone_number`.
   - `LocationPreferencesForm`: Handles multi-select `area_preference`, `budget_min`, `budget_max`.
   - `PasswordChangeForm`: Handles `current_password`, `new_password`, `confirm_password`.
2. `apps/accounts/views.py`:
   - `AccountSettingsView(LoginRequiredMixin, View)`: GET renders all 3 section cards/forms; POST dispatches to appropriate form submission handler based on form identifier.
3. `templates/accounts/settings.html`:
   - Profile summary header with avatar placeholder, email, verification pill badge, and account join date.
   - Section 1: Profile Details (display name, phone number).
   - Section 2: Location & Search Preferences (13 Dhaka sub-area chip selector, budget inputs).
   - Section 3: Account Security (password change).
4. `templates/basha/partials/navbar.html`:
   - Add "Account Settings" item with gear icon (`bi-gear`) to user dropdown.

---

## Success Criteria & Test Boundaries

- Integration test verifying unauthenticated access redirects to `/login/?next=/accounts/settings/`.
- Integration test verifying GET `/accounts/settings/` populates forms with user's current data.
- Integration test verifying successful profile update displays flash success message.
- Integration test verifying area selection persists and updates feed matching compatibility scores.
- Integration test verifying password change preserves logged-in session.
