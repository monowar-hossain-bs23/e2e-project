---
intent: 006-account-settings-and-preferences
phase: inception
status: complete
created: '2026-11-01T10:15:00Z'
updated: '2026-11-01T11:56:00Z'
---

# Requirements: Account Settings with Location Preference Update

## Intent Overview

Enable authenticated Basha Pass tenants and flat seekers to manage their account profile (display name, contact phone number), security settings (password change), and independently update their target living location preferences (Dhaka sub-areas) and budget range. This keeps listing compatibility recommendations fresh and accurate without invalidating verified Tenant Passport credentials.

---

## Business Goals

| Goal | Success Metric | Priority |
|------|----------------|----------|
| User Self-Service | Tenants can manage profile details and contact phone without admin intervention | Must |
| Dynamic Match Scoring | Updated Dhaka sub-areas and budget immediately refresh 6-axis compatibility dots across feed cards | Must |
| Passport Verification Integrity | Preserving NID audit trail while allowing flexible location preference changes without voiding verification | Must |
| Account Security | In-app password rotation with session preservation and complexity validation | Must |

---

## User Personas

1. **Flat Seeker (Verified or In-Review)**: Wants to expand or refine their target living zones (e.g. moving search from Mirpur to Dhanmondi/Mohammadpur) and adjust budget range to see updated compatibility scores on listings.
2. **Accommodation Lister (Host)**: Wants to update their direct contact phone number displayed to verified viewers without having to edit individual listings one-by-one.
3. **General Tenant**: Wants to update their public handle (`display_name`) or rotate their account password securely.

---

## Functional Requirements

### FR-1: Account Settings Hub & Navigation
- **Description**: Provide a central, authenticated hub view at `/accounts/settings/` (named `account_settings`), accessible from the main navigation user dropdown.
- **Acceptance Criteria**:
  - Accessible only to authenticated users (anonymous redirected to login with `next` parameter).
  - Organized with tabbed or sectioned cards: Profile Information, Location & Budget Preferences, and Security / Password.
  - Displays user identity summary: registered email (read-only), current verification status badge (Verified, In Review, Unverified), and account member since date.
- **Priority**: Must

### FR-2: Profile Information Management
- **Description**: Allow users to update their public-facing display name and primary contact phone number.
- **Acceptance Criteria**:
  - `display_name` is validated against 2–32 characters and permitted character set regex (`^[A-Za-z0-9 ._\-']+$`).
  - `phone_number` is validated against Bangladeshi mobile phone format (`01[3-9]\d{8}`, `+8801[3-9]\d{8}`, `8801[3-9]\d{8}`) and international phone formats.
  - Submitting valid changes updates `User.display_name` and `User.phone_number`.
  - Updated phone number is immediately reflected in the contact disclosure cards of authored listings for verified viewers.
- **Priority**: Must

### FR-3: Location Preferences and Budget Updates
- **Description**: Allow users with a `LifestyleProfile` (both verified tenants and unverified/in-review users) to update their preferred Dhaka sub-areas and monthly budget range.
- **Acceptance Criteria**:
  - Form displays multi-select chip/checkbox picker with canonical 13 Dhaka sub-areas (`DHAKA_SUB_AREAS`).
  - Validates that selected areas are non-empty and a valid subset of canonical Dhaka areas via `validate_dhaka_sub_areas`.
  - Captures `budget_min` (৳500+) and `budget_max` (up to ৳50,000) enforcing `budget_min <= budget_max`.
  - **Decoupled Immutability Invariant**: Updates to `area_preference`, `budget_min`, and `budget_max` are permitted for verified tenants without invalidating their verification status or triggering `ValidationError`. Core identity dimensions (gender, smoking, sleep schedule) remain protected.
  - Updates persist to `LifestyleProfile` and immediately recalculate 6-axis compatibility scores on `/listings/` feed cards and detail pages.
- **Priority**: Must

### FR-4: Security / Password Change
- **Description**: Secure in-app password update mechanism requiring current password verification and enforcing password complexity standards.
- **Acceptance Criteria**:
  - Form requires current password, new password, and new password confirmation.
  - Validates current password using `user.check_password()`.
  - Validates new password against `PasswordComplexityValidator` (min 8 chars, uppercase, lowercase, number, special symbol).
  - Verifies new password and confirmation match.
  - On valid submission, updates password with `user.set_password()` and calls `update_session_auth_hash(request, user)` so user session remains active.
  - Emits security notification message upon completion.
- **Priority**: Must

### FR-5: Append-Only Security Audit Logging
- **Description**: Record security and profile updates in the platform's tamper-evident audit ledger.
- **Acceptance Criteria**:
  - Whenever a user updates their contact phone number or rotates their password, an `AuditEntry` is created via `AuditService.append`.
  - Password hashes are never written to audit state dictionaries.
- **Priority**: Should

---

## Non-Functional Requirements

### Performance
| Requirement | Metric | Target |
|-------------|--------|--------|
| Settings Page Load | p95 server render time | < 120ms |
| Profile & Preference Save | p95 transaction duration | < 150ms |
| Query Efficiency | ORM query count | Max 2 queries (eager join on passport & lifestyle profile) |

### Security & Privacy
- **Owner-Scoped Mutability**: Views and form handlers mutate only `request.user` and `request.user.passport.lifestyle_profile`. URL structure does not accept user IDs, preventing IDOR vulnerabilities.
- **Credential Protection**: CSRF protection on all forms; passwords never serialized into error logs or audit entries.
- **PII Integrity**: Phone number stored securely and soft-gated by `ConsentService` when rendered across the platform.

### User Experience
- **Responsive Layout**: Works seamlessly across mobile, tablet, and desktop viewports.
- **Real-Time Visual Validation**: Area multi-selection chips highlight clearly when selected.
- **Feedback**: Instant toast/banner confirmation alerts using Bootstrap 5 alerts and icons.

---

## Acceptance Test Scenarios

1. **Scenario 1: Update Location Preferences & Verify Feed Match**:
   - Given a verified tenant whose preferred area is "Mirpur",
   - When they navigate to Account Settings and change preferred areas to `["Dhanmondi", "Mohammadpur"]`,
   - Then the settings page confirms success,
   - And viewing the feed shows listings in Dhanmondi matching the location axis in 6-axis compatibility scores.

2. **Scenario 2: Update Contact Phone Number**:
   - Given an author with an active room listing,
   - When they update their contact phone number in Account Settings to `+8801799998888`,
   - Then viewing their listing as a verified seeker displays the new number `+8801799998888`.

3. **Scenario 3: Password Rotation**:
   - Given an authenticated tenant,
   - When they submit current password with a new valid complex password,
   - Then password is updated and their active session remains authenticated.
   - When logging in again later, the new password is required.
