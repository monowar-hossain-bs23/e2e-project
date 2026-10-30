---
id: 001-core-foundation
unit: 001-core-foundation
intent: 001-project-init-and-landing
type: simple-construction-bolt
status: complete
stories:
  - 001-django-project-scaffolding
  - 002-base-layout-and-design-tokens
created: '2026-10-30T07:33:30Z'
started: '2026-10-30T08:02:11Z'
completed: '2026-10-30T08:13:33Z'
current_stage: null
stages_completed:
  - name: plan
    completed: '2026-10-30T08:04:14Z'
    artifact: implementation-plan.md
  - name: implement
    completed: '2026-10-30T08:11:56Z'
    artifact: implementation-walkthrough.md
  - name: test
    completed: '2026-10-30T08:13:33Z'
    artifact: test-walkthrough.md
requires_bolts: []
enables_bolts:
  - 002-landing-page-ui
requires_units: []
blocks: false
complexity:
  avg_complexity: 1
  avg_uncertainty: 1
  max_dependencies: 1
  testing_scope: 2
---

# Bolt: 001-core-foundation

## Overview
Foundational scaffolding for Basha Pass: Poetry packaging, Django 5.2 layout, environment configuration via `django-environ`, Ruff linter/formatter, pytest test harness, and base HTML template with design system tokens.

## Objective
Establish a clean, robust, and reproducible development and testing baseline for the entire application, ensuring brand CSS tokens and basic configuration are rock-solid.

## Stories Included
- **001-django-project-scaffolding**: Setup Poetry, Django 5.2, split settings, and test harness (Must)
- **002-base-layout-and-design-tokens**: Base HTML template with brand tokens and responsive layout structure (Must)

## Bolt Type
**Type**: Simple Construction Bolt
**Definition**: `.specsmd/aidlc/templates/construction/bolt-types/simple-construction-bolt.md`

## Stages
- ✅ **1. Plan**: Complete → `implementation-plan.md`
- ✅ **2. Implement**: Complete → `implementation-walkthrough.md`
- ✅ **3. Test**: Complete → `test-walkthrough.md`

## Dependencies

### Requires
- None

### Enables
- `002-landing-page-ui`

## Success Criteria
- [x] Poetry environment configured and dependencies installed
- [x] `python manage.py check` reports 0 issues
- [x] Ruff format and lint checks pass cleanly
- [x] `pytest` discovers and passes initial test suite
- [x] `base.html` embeds brand tokens matching `docs/mockups/01-landing.html`
