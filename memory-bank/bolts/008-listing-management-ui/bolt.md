---
id: 008-listing-management-ui
unit: 002-listing-authoring-and-management-ui
intent: 004-create-and-manage-listing
type: simple-construction-bolt
status: planned
stories:
  - 020-verified-tenant-listing-gate
  - 021-listing-create-form-and-view
  - 022-lister-management-dashboard
  - 023-listing-edit-and-withdraw-views
created: '2026-10-31T07:30:00Z'
started: null
completed: null
current_stage: null
stages_completed: []
requires_bolts:
  - 007-listing-domain-service
enables_bolts: []
requires_units:
  - 001-listing-domain-service
blocks: true
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 1
  testing_scope: 2
---

# Bolt: 008-listing-management-ui

## Overview
Presentation layer and user dashboard for Basha Pass accommodation listing authoring and management: `VerifiedTenantRequiredMixin` gating authoring views, `ListingCreateView` and `ListingCreationForm` supporting multi-section creation, cross-field validation, photo uploader with aspect ratio advisory note, and 3-active cap warnings; `ListerDashboardView` ("Your Listings") with status badges (**Active**, **Withdrawn**, **Archived**) and filter tabs; `ListingEditView` for mutable terms; and `ListingWithdrawView` with modal confirmation.

## Objective
Deliver a responsive, user-friendly listing creation and management experience for verified tenants, reinforcing brand identity and providing clear feedback on platform rules per PRD §4.4 and mockups (02-dashboard-hub, 05-listing-create).

## Stories Included
- **020-verified-tenant-listing-gate**: Authorization guard mixin enforcing `passport.status == 'verified'`, redirecting unverified/pending tenants with instructional flash messages (Must)
- **021-listing-create-form-and-view**: Multi-section creation form at `/listings/create/`, active cap banner, and photo uploader with landscape aspect ratio guidance (Must)
- **022-lister-management-dashboard**: "Your Listings" dashboard view with status badges, active/archived toggle tabs, and quick actions (Must)
- **023-listing-edit-and-withdraw-views**: Edit view for mutable fields, locked-field protection, and manual withdrawal modal action (Must)

## Bolt Type
`simple-construction-bolt` (Follows 3 stages: Plan → Implement → Test)
