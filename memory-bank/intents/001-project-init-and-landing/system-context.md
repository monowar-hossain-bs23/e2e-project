---
intent: 001-project-init-and-landing
phase: inception
status: context-defined
updated: 2026-10-30T07:33:30Z
---

# 001-project-init-and-landing - System Context

## System Overview

Basha Pass is a verified roommate and seat-matching web application for urban Bangladesh. This foundational intent establishes the project runtime infrastructure (Python 3.12, Django 5.2, Poetry, Ruff, pytest), modular configurations, base layout templates with design system tokens (Trust Teal `#0F6E7A`, Warm Secondary `#C56B4F`), and delivers the public landing page matching the visual mockup at `docs/mockups/01-landing.html`.

## Actors

- **Public Visitor / Seeker** (Human): Prospective renter in Dhaka exploring room/seat availability and evaluating the "Tenant Passport" trust proposition.
- **Prospective Lister** (Human): Current renter/tenant looking for compatible roommates or mess seat replacements.
- **Developer / Agent** (System/Human): AI agents and human developers maintaining the codebase and preparing upcoming bounded contexts.

## External Systems & CDN Integrations

- **Bootstrap 5.3 CDN**: Provides vanilla grid, layout, and utility classes, re-painted with Basha Pass design tokens via CSS custom properties.
- **Bootstrap Icons CDN**: Delivers standard iconography (shield-check, person, house, search) for UI affordances.
- **PostgreSQL Database**: Configured for data persistence (ready for future context models).

## High-Level Constraints

- UI is strictly English-only in v1 (per PRD §2.1).
- Public URLs must not require authentication (`config/urls_public.py`).
- Design system variables must match `docs/mockups/01-landing.html` and `DESIGN.md`.

## Key NFR Goals

- Fast first-contentful paint (<100ms local server response).
- Zero console errors and clean responsive layout across mobile (<768px) and desktop (>=1200px) displays.

## Context Diagram

```mermaid
graph TD
    Visitor["Public Visitor / Seeker"] -->|Browses Landing Page (HTTP GET /)| DjangoApp["Basha Pass (Django 5.2 + HTMX)"]
    Lister["Prospective Lister"] -->|Reviews How It Works| DjangoApp
    DjangoApp -->|Loads Icons & Grid| CDNs["Bootstrap 5.3 & Bootstrap Icons CDN"]
    DjangoApp -->|Prepares Connection| Postgres["PostgreSQL Database"]
    DjangoApp -->|Routes to Signup / Login| AuthPlaceholders["Identity Routes (/accounts/*)"]
```
