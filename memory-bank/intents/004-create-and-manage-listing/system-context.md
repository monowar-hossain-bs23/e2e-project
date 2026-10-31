---
intent: 004-create-and-manage-listing
phase: inception
status: context-defined
updated: '2026-10-31T07:20:00Z'
---

# 004-create-and-manage-listing - System Context

## System Overview

The **Listing Creation & Management** capability enables verified tenants in Dhaka to author, publish, update, and withdraw supply-side rental listings for available seats in a mess or private rooms. It serves as the primary supply engine for the Basha Pass marketplace, enforcing verified-only creation, cross-field integrity between accommodation kind and rent unit, a hard 3-active listing limit, and automatic archival.

## Context Diagram

```mermaid
flowchart TD
    subgraph Users
        VT["Verified Tenant\n(Author)"]
        UV["Unverified / Pending Tenant"]
    end

    subgraph BashaPassSystem["Basha Pass Platform (Intent 004)"]
        subgraph Gating["Access Control"]
            Gate["Verified Tenant Gate\n(FR-1)"]
        end

        subgraph AuthoringUI["Authoring & Management UI"]
            CreateForm["Listing Creation Form\n(FR-3)"]
            PhotoUpload["Photo Uploader UI\n(FR-4)"]
            ListerDash["Your Listings Dashboard\n(FR-5)"]
            EditWithdraw["Edit & Withdraw Views\n(FR-6, FR-7)"]
        end

        subgraph CoreDomain["Listing Domain Aggregate"]
            ListingModel["Listing & ListingPhoto Models\n(UUIDv7 PK, 13 Areas)"]
            ListingSvc["ListingService (AD-6)\n(Create, Invariants, 3-Cap,\nEdit, Withdraw, Auto-Archive)"]
            PhotoStorage["ListingPhotoStorageService\n(Pillow validation, public media)"]
        end
    end

    subgraph ExternalAndShared["Shared Platform Dependencies"]
        PassportCtx["Passport Aggregate\n(apps.passports - Status == VERIFIED)"]
        AuditCtx["AuditService (AD-15)\n(apps.audit - Append-Only Log)"]
        MediaDisk["Media Storage\n(media/listings/photos/)"]
        CronRunner["Management Command / Cron\n(archive_stale_listings)"]
    end

    VT -->|Accesses /listings/create/| Gate
    UV -->|Access attempt blocked| Gate
    Gate -->|Authorized| CreateForm
    Gate -->|Redirects with prompt| PassportCtx

    CreateForm --> PhotoUpload
    CreateForm --> ListingSvc
    PhotoUpload --> PhotoStorage
    PhotoStorage --> MediaDisk

    VT -->|Views authored posts| ListerDash
    ListerDash --> EditWithdraw
    EditWithdraw --> ListingSvc

    ListingSvc --> ListingModel
    ListingSvc --> AuditCtx
    ListingSvc --> PassportCtx
    CronRunner -->|Daily trigger| ListingSvc
```

## External & Cross-Context Integrations

- **Passport Context (`apps.passports`)**: Enforces pre-condition that author holds `passport.status == 'verified'`. Foreign key `author_id` references `Passport.id` (ON DELETE RESTRICT per ERD §4).
- **Audit Context (`apps.audit`)**: Captures immutable audit entries for all listing lifecycle mutations (create, edit, withdraw, and 60-day auto-archive).
- **Media Storage Engine**: Stores public listing photos under `media/listings/photos/<listing_id>/` at upload resolution after validating MIME type, file size (≤5MB), and magic bytes.
- **Django Management & Scheduling**: Custom command `archive_stale_listings` executes `ListingService.archive_stale()` periodically to auto-archive posts older than 60 days.

## High-Level Constraints

- **AD-6 ListingService Invariant Authority**: All mutations (`create`, `edit`, `withdraw`, `archive_stale`) must flow exclusively through `ListingService`. Direct ORM writes bypassing the service are strictly forbidden.
- **Mutual Consistency**: Accommodation `kind == 'seat'` requires `rent_unit == 'per_seat'`; `kind == 'room'` requires `rent_unit == 'per_room'`. `rent_period` is permanently fixed to `per_month`.
- **Anti-Spam 3-Active Limit**: A verified tenant can have at most 3 active (non-archived, non-withdrawn) listings at any given time.
- **Post-Publish Immutability**: Location `area` and accommodation `kind` cannot be altered once published. Only rent terms, body notes, and photos can be edited.

## Key NFR Goals

- **Execution Latency**: Form submission and service mutations complete in < 300ms.
- **Safety**: Robust file payload inspection (magic bytes / Pillow) rejecting corrupt or executable uploads.
- **Zero Public PII Leakage**: The authoring domain only captures listing descriptions and photos. Contact details are soft-gated on view surfaces (governed by `ConsentService` in feed intent).
