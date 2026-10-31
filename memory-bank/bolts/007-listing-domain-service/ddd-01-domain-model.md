---
unit: 001-listing-domain-service
bolt: 007-listing-domain-service
stage: model
status: complete
created: '2026-10-31T07:40:00Z'
---

# Static Model: 001-listing-domain-service

## Bounded Context

This unit belongs to the **Listing Context (`apps.listings`)**, the supply-side marketplace engine of Basha Pass. It integrates with three existing platform contexts:

1. **Passport Context (`apps.passports`)**: Supplies the verified tenant aggregate root (`Passport`). A listing cannot exist without a valid, verified passport (`author.status == 'verified'`).
2. **Audit Context (`apps.audit`)**: Captures compliance entries across all listing lifecycle transitions (`create`, `edit`, `withdraw`, `archive_stale`).
3. **Public Media Storage Engine**: Persists public listing photos in `media/listings/photos/<listing_id>/`.

```mermaid
graph TD
    subgraph IdentityContext ["Identity Context (apps.accounts)"]
        User["User (UUID4 PK)"]
    end

    subgraph PassportContext ["Passport Context (apps.passports)"]
        Passport["Passport (Aggregate Root)\nStatus: VERIFIED required"]
        User -->|1:1| Passport
    end

    subgraph ListingContext ["Listing Context (apps.listings)"]
        Listing["Listing (Aggregate Root, UUIDv7 PK)"]
        ListingPhoto["ListingPhoto (Child Entity, 1–7 items)"]
        ListingSvc["ListingService (Sole Mutator, AD-6)"]
        PhotoStorage["ListingPhotoStorageService (Pillow, Public Media)"]
        
        Listing -->|1:N CASCADE (1..7)| ListingPhoto
        ListingSvc -->|Mutates Lifecycle| Listing
        ListingSvc -->|Persists Images| PhotoStorage
        ListingSvc -->|Verifies Status| Passport
    end

    subgraph AuditContext ["Audit Context (apps.audit)"]
        AuditEntry["AuditEntry (Append-Only)"]
        AuditSvc["AuditService (AD-15)"]
        
        AuditSvc -->|Logs mutations| AuditEntry
        ListingSvc -->|Transacts via| AuditSvc
    end

    Passport -->|1:N RESTRICT| Listing
```

---

## Domain Entities

| Entity | Properties | Business Rules & Invariants |
|---|---|---|
| `Listing` | `id` (UUIDv7 PK)<br/>`author_id` (FK → `Passport.id`, ON DELETE RESTRICT)<br/>`kind` (`ListingKind`: `seat`, `room`)<br/>`rent_bdt` (`PositiveInteger`, 500–50,000)<br/>`rent_unit` (`RentUnit`: `per_seat`, `per_room`)<br/>`rent_period` (`RentPeriod`: `per_month` fixed)<br/>`area` (`list[DhakaSubArea]`, cardinality 1–13)<br/>`body` (`text`, nullable, ≤500 chars)<br/>`pref_gender` (`GenderEnum`: `male`, `female`, `any`)<br/>`pref_smoking` (`SmokingEnum`: `yes`, `no`, `any`)<br/>`pref_sleep` (`SleepScheduleEnum`: `early_bird`, `night_owl`, `flexible`)<br/>`pref_occupation` (`list[OccupationEnum]`, canonical set)<br/>`created_at` (`datetime`)<br/>`archived_at` (`datetime`, nullable)<br/>`withdrawn_at` (`datetime`, nullable) | - **Verified Author Precondition (FR-10)**: Author's passport MUST have `status == 'verified'`.<br/>- **3-Active Cap (FR-12, AD-6)**: At most 3 active (`archived_at IS NULL AND withdrawn_at IS NULL`) listings per tenant.<br/>- **Kind/Unit Equivalence**: `kind == 'seat'` requires `rent_unit == 'per_seat'`; `kind == 'room'` requires `rent_unit == 'per_room'`.<br/>- **Fixed Rent Period**: `rent_period` is permanently `'per_month'` (never user-configurable in v1).<br/>- **Area Constraint**: Non-empty subset of the 13 canonical Dhaka sub-areas.<br/>- **Post-Publish Immutability (AD-6)**: `kind` and `area` cannot be changed after creation. |
| `ListingPhoto` | `id` (UUID4 PK)<br/>`listing_id` (FK → `Listing.id`, ON DELETE CASCADE)<br/>`photo_path` (`str`, relative storage path)<br/>`order` (`PositiveSmallInteger`, 0–6)<br/>`created_at` (`datetime`) | - **Cardinality Constraint (FR-10)**: Every listing MUST have between 1 and 7 photos.<br/>- Stored at original upload resolution (no mandatory cropping).<br/>- Photo paths point to public media `listings/photos/<listing_id>/<uuid>.<ext>`.<br/>- Cascade deletes physical files from disk upon deletion. |

---

## Value Objects

| Value Object | Properties | Constraints & Rules |
|---|---|---|
| `Rent` | `amount`: `int` (BDT)<br/>`unit`: `RentUnit` (`per_seat`, `per_room`)<br/>`period`: `RentPeriod` (`per_month`) | - `500 <= amount <= 50,000`.<br/>- Immutable value object.<br/>- Formats currency display (e.g., `৳8,500/seat`). |
| `DhakaSubArea` | Canonical set of 13 areas | `['Azimpur', 'Badda', 'Banani', 'Dhanmondi', 'Gulshan', 'Khilgaon', 'Mirpur', 'Mohakhali', 'Mohammadpur', 'Old Dhaka', 'Rampura', 'Shantinagar', 'Uttara']`. |
| `RoommatePreferences` | `gender`: `male` \| `female` \| `any`<br/>`smoking`: `yes` \| `no` \| `any`<br/>`sleep`: `early_bird` \| `night_owl` \| `flexible`<br/>`occupations`: `list[str]` | - Validates compatibility criteria against standard platform lifestyle dimensions. |

---

## Aggregates

### Aggregate Root: `Listing`
- **Boundary**: `Listing` acts as the aggregate root governing its `ListingPhoto` child collection.
- **Invariants Enforced at Root**:
  1. Author eligibility: author must hold verified passport status.
  2. Active listing cap: author cannot exceed 3 active listings.
  3. Photo collection invariant: `1 <= len(listing.photos) <= 7`. Photos cannot exist without their parent Listing.
  4. Cross-field consistency: `kind` matches `rent_unit`.
  5. Immutability guard: mutating `kind` or `area` post-publish is rejected.

---

## Domain Events

| Event Name | Trigger | Payload |
|---|---|---|
| `ListingCreated` | New listing successfully persisted via `ListingService.create()` | `listing_id`, `author_id`, `kind`, `rent_bdt`, `area`, `created_at` |
| `ListingEdited` | Mutable fields updated via `ListingService.edit()` | `listing_id`, `author_id`, `changed_fields`, `updated_at` |
| `ListingWithdrawn` | Author marks listing inactive via `ListingService.withdraw()` | `listing_id`, `author_id`, `withdrawn_at` |
| `ListingArchived` | Background worker marks listings > 60 days old | `listing_id`, `author_id`, `archived_at` |

---

## Domain Services

### 1. `ListingService` (AD-6 Sole Mutator)
Encapsulates all write operations and state transitions for the Listing domain:
- `create(author, *, kind, rent_bdt, rent_unit, area, body, pref_gender, pref_smoking, pref_sleep, pref_occupation, photo_files)`:
  1. Verifies `author.status == Passport.Status.VERIFIED`.
  2. Atomically checks active cap (`count < 3`) using `select_for_update()`.
  3. Enforces `kind ↔ rent_unit` parity and `rent_period == 'per_month'`.
  4. Saves photos via `ListingPhotoStorageService`.
  5. Persists `Listing` and `ListingPhoto` records in a transaction.
  6. Emits `AuditEntry` logging creation.
- `edit(listing, *, actor, fields)`:
  - Verifies `actor == listing.author.user` (or staff).
  - Validates that only mutable fields (`rent_bdt`, `rent_unit`, `body`, photos) are updated.
  - Rejects attempts to alter `kind` or `area` with `{ok: False, code: 'field_locked'}`.
  - Emits `AuditEntry` logging update.
- `withdraw(listing, *, actor)`:
  - Verifies ownership, stamps `withdrawn_at = timezone.now()`, emits `AuditEntry`.
- `archive_stale()`:
  - Queries active listings older than 60 days, stamps `archived_at = timezone.now()`, emits `AuditEntry`.

### 2. `ListingPhotoStorageService`
- `validate_photo_batch(files)`: Checks count (1–7), sizes (≤5MB each), MIME types, and Pillow file integrity.
- `save_photo(file, listing_id, order)`: Saves to `media/listings/photos/<listing_id>/<uuid>.<ext>`.
- `delete_photo(photo)`: Removes the physical file from disk.

---

## Repository Interfaces

```python
class ListingRepository:
    """Contract for querying and filtering listings."""

    def count_active_by_author(self, passport: Passport) -> int:
        """Count listings where archived_at is null and withdrawn_at is null."""
        ...

    def get_stale_active_listings(self, days: int = 60) -> QuerySet[Listing]:
        """Find active listings created more than `days` ago."""
        ...

    def get_lister_listings(
        self, passport: Passport, include_archived: bool = True
    ) -> QuerySet[Listing]:
        """Query listings authored by passport, ordered newest first."""
        ...
```

---

## Ubiquitous Language Glossary

| Term | Definition |
|---|---|
| **Listing** | A supply-side marketplace post representing an available room or seat for rent in Dhaka. |
| **Seat** | An accommodation arrangement where a tenant rents a specific bed/seat within a shared room in a mess or flat. Requires `rent_unit == 'per_seat'`. |
| **Room** | A private individual bedroom rented within an apartment or house. Requires `rent_unit == 'per_room'`. |
| **Rent Unit** | Pricing denominator (`per_seat` or `per_room`). |
| **Rent Period** | Billing interval, permanently fixed to `per_month` in v1. |
| **Active Listing** | A listing currently live and open for seekers (`archived_at IS NULL AND withdrawn_at IS NULL`). Counts against the 3-active limit. |
| **Withdrawn Listing** | A listing manually removed by the author (`withdrawn_at IS NOT NULL`). Excluded from active caps. |
| **Archived Listing** | A listing automatically retired after 60 days (`archived_at IS NOT NULL`). Excluded from active caps. |
| **Active Cap (3-Cap)** | Anti-spam platform rule restricting each verified tenant to at most 3 active listings at any time. |
