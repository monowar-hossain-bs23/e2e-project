---
id: 002-landing-page-ui
unit: 002-landing-page-ui
intent: 001-project-init-and-landing
type: simple-construction-bolt
status: complete
stories:
  - 003-landing-hero-and-passport-showcase
  - 004-how-it-works-and-navigation
created: '2026-10-30T07:33:30Z'
started: '2026-10-30T08:16:42Z'
completed: '2026-10-30T08:39:24Z'
current_stage: null
stages_completed:
  - name: plan
    completed: '2026-10-30T08:19:20Z'
    artifact: implementation-plan.md
  - name: implement
    completed: '2026-10-30T08:24:10Z'
    artifact: implementation-walkthrough.md
  - name: test
    completed: '2026-10-30T08:39:24Z'
    artifact: test-walkthrough.md
requires_bolts:
  - 001-core-foundation
enables_bolts: []
requires_units:
  - 001-core-foundation
blocks: false
complexity:
  avg_complexity: 2
  avg_uncertainty: 1
  max_dependencies: 2
  testing_scope: 2
---

# Bolt: 002-landing-page-ui

## Overview
Implementation of the public Basha Pass landing page served at root `/`, matching the visual specification and interactive sections of `docs/mockups/01-landing.html`.

## Objective
Deliver a responsive, high-trust landing page featuring the hero section, search/filter teaser, visual Tenant Passport showcase, 3-step process guide, trust explainer, navbar, and footer.

## Stories Included
- **003-landing-hero-and-passport-showcase**: Hero section, search filter teaser, and Tenant Passport showcase card (Must)
- **004-how-it-works-and-navigation**: Navigation navbar, "How It Works" steps, trust panel, and footer (Must)

## Bolt Type
**Type**: Simple Construction Bolt
**Definition**: `.specsmd/aidlc/templates/construction/bolt-types/simple-construction-bolt.md`

## Stages
- ✅ **1. Plan**: Complete → `implementation-plan.md`
- ✅ **2. Implement**: Complete → `implementation-walkthrough.md`
- ✅ **3. Test**: Complete → `test-walkthrough.md`

## Dependencies

### Requires
- `001-core-foundation`

### Enables
- Prepares UI entry points for future user authentication and verification intents

## Success Criteria
- [x] `GET /` returns HTTP 200 with complete rendered HTML
- [x] Visual fidelity matches `docs/mockups/01-landing.html`
- [x] Navigation and CTAs correctly link to targets or placeholder routes
- [x] `pytest` integration tests confirm page render and content assertions
