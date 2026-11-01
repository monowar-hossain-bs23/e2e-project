---
id: 012-account-settings-ui
unit: 002-account-settings-ui
intent: 006-account-settings-and-preferences
type: simple-construction-bolt
status: complete
stories:
  - 031-account-settings-hub-and-profile-form-ui
  - 032-location-preference-and-password-change-ui
created: '2026-11-01T11:46:00Z'
started: '2026-11-01T12:14:00Z'
completed: '2026-11-01T12:37:00Z'
current_stage: test
stages_completed:
  - name: plan
    completed: '2026-11-01T12:15:00Z'
    artifact: implementation-plan.md
  - name: implement
    completed: '2026-11-01T12:24:00Z'
    artifact: implementation-walkthrough.md
  - name: test
    completed: '2026-11-01T12:35:00Z'
    artifact: test-walkthrough.md
requires_bolts:
  - 011-account-preference-domain
enables_bolts: []
requires_units:
  - 001-account-preference-domain
blocks: true
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 1
  testing_scope: 2
---

# Bolt: 012-account-settings-ui

## Overview

User-facing presentation and interaction layer for tenant account settings. Implements the `/accounts/settings/` view, profile card (display name and contact phone), interactive Dhaka sub-area chip selector, budget inputs, secure password rotation form, toast alerts, and navbar integration.

## Objective

Deliver an intuitive, responsive, and secure self-service settings experience matching the Basha Pass design system, allowing tenants to manage their identity, evolve their search zones, and secure their credentials effortlessly per PRD §4.2, §4.5.

## Stories Included

- **031-account-settings-hub-and-profile-form-ui**: Gated Account Settings hub view, profile card with display name & phone form, navbar link (Must)
- **032-location-preference-and-password-change-ui**: Dhaka sub-area chip selector, budget inputs, and secure password change form (Must)

## Verification Plan

- Authentication gating tests verifying anonymous users are redirected to login with `next` parameter.
- GET tests verifying current user data pre-populates all form fields and area chips.
- Form submission tests verifying individual form handling and flash message dispatch.
- End-to-end integration tests verifying updated location preferences refresh 6-axis compatibility scores on `/listings/`.
- Navbar tests verifying "Account Settings" item is rendered for authenticated users.
