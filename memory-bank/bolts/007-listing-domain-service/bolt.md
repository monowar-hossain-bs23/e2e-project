---
id: 007-listing-domain-service
unit: 001-listing-domain-service
intent: 004-create-and-manage-listing
type: ddd-construction-bolt
status: planned
stories:
  - 017-listing-and-photo-models
  - 018-listing-service-and-active-cap
  - 019-listing-photo-storage-service
created: '2026-10-31T07:30:00Z'
started: null
completed: null
current_stage: null
stages_completed: []
requires_bolts:
  - 005-passport-verification-service
enables_bolts:
  - 008-listing-management-ui
requires_units:
  - 001-passport-and-verification-domain
blocks: false
complexity:
  avg_complexity: 3
  avg_uncertainty: 2
  max_dependencies: 2
  testing_scope: 2
---

# Bolt: 007-listing-domain-service

## Overview
Domain models, database-level constraints, storage engine, and mutating service governing Basha Pass rental listings: `Listing` aggregate root (UUIDv7, kind enum, rent constraints, area array, lifestyle preferences), `ListingPhoto` child entity, `ListingPhotoStorageService` managing public media persistence (1–7 images, JPEG/PNG/WebP, max 5MB, magic byte validation), `ListingService` sole mutator enforcing verified author precondition, atomic 3-active listing cap check, locked-field edits (`kind` and `area` immutable), manual withdrawal, and 60-day auto-archive management command, with full append-only `AuditEntry` tracking.

## Objective
Establish the foundational supply-side inventory domain for Basha Pass, guaranteeing high-integrity accommodation posts, robust abuse mitigation via the 3-active listing cap, and durable auditability per PRD §4.4, ERD §4, and Architecture Spine AD-6, AD-9, AD-15.

## Stories Included
- **017-listing-and-photo-models**: `Listing` & `ListingPhoto` domain models with UUIDv7 PK, cross-field constraints, area array, and preference axes (Must)
- **018-listing-service-and-active-cap**: `ListingService` sole mutator, 3-active cap check, edit locked fields, withdraw, auto-archive, and audit trail (Must)
- **019-listing-photo-storage-service**: `ListingPhotoStorageService` validating 1–7 photos, Pillow structure checks, public media storage, and deletion cleanup (Must)

## Bolt Type
`ddd-construction-bolt` (Requires 4 stages: Domain Model → Technical Design & ADR → Implement → Test Report)
