---
unit: 001-listing-domain-service
bolt: 007-listing-domain-service
stage: design
status: complete
updated: '2026-10-31T07:50:00Z'
---

# Technical Design: 001-listing-domain-service

## Architecture Pattern

**Domain-Driven Layered Architecture with Service Spine (AD-1, AD-6, AD-9, AD-15)**:
The Listing domain represents the supply-side marketplace catalog within `apps.listings`. The architecture strictly follows the system-wide service spine pattern:
- **`Listing` Aggregate Root & `ListingPhoto` Entity**: Captures data constraints, area arrays, and accommodation dimensions.
- **`ListingService` (AD-6 Sole Mutator)**: All creation, updates, withdrawal, and archival operations flow exclusively through `ListingService`. Direct ORM writes from views or admin are prohibited.
- **`ListingPhotoStorageService`**: Validates file security (magic bytes/Pillow, MIME, ≤5MB) and persists public images under `media/listings/photos/<listing_id>/`.
- **`AuditService` Integration (AD-15)**: Append-only compliance log recording every state transition.

## Layer Structure

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Admin & CLI Layer                                                      │
│ - apps/listings/admin.py: Django Admin read-only invariant views       │
│ - apps/listings/management/commands/archive_stale_listings.py: Cron   │
├────────────────────────────────────────────────────────────────────────┤
│ Application / Domain Service Layer                                     │
│ - apps/listings/services/listing_service.py: Sole mutator (AD-6)       │
│ - apps/listings/services/storage.py: ListingPhotoStorageService        │
│ - apps/audit/services/audit_service.py: Append-only audit logger (AD-15)│
├────────────────────────────────────────────────────────────────────────┤
│ Domain Layer                                                           │
│ - apps/listings/constants.py: ListingKind, RentUnit, RentPeriod enums  │
│ - apps/listings/validators.py: Rent bounds & cross-field validators   │
├────────────────────────────────────────────────────────────────────────┤
│ Persistence & Storage Layer                                            │
│ - apps/listings/models.py: Listing (UUIDv7), ListingPhoto (UUID4)      │
│ - media/listings/photos/: Public media root                            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Data Persistence & Schema (ERD §4)

### 1. `Listing` Model (`apps.listings.models.Listing`)

| Column | Type | Constraints & Attributes | Description |
|---|---|---|---|
| `id` | `UUIDField` | Primary Key, default `uuid.uuid4` (or UUIDv7), editable=False | Unique identifier for accommodation post |
| `author` | `ForeignKey` | `passports.Passport`, `on_delete=models.RESTRICT`, `related_name="listings"` | Must belong to a verified Passport |
| `kind` | `CharField(8)` | Choices: `seat` ("Seat"), `room` ("Room"), `db_index=True` | Type of accommodation offered |
| `rent_bdt` | `PositiveIntegerField` | Bounded: ৳500 to ৳50,000 | Monthly rent amount in Bangladeshi Taka |
| `rent_unit` | `CharField(16)` | Choices: `per_seat`, `per_room` | Rent unit (enforced equal to kind) |
| `rent_period` | `CharField(16)` | Default `'per_month'`, fixed | Rent billing period |
| `area` | `JSONField` | Default `list`, `validators=[validate_dhaka_sub_areas]` | 1 to 13 canonical Dhaka sub-areas |
| `body` | `TextField` | Nullable, blank, max_length=500 | Optional host notes (supports Bengali) |
| `pref_gender` | `CharField(16)` | Choices: `male`, `female`, `any` | Preferred roommate gender |
| `pref_smoking` | `CharField(16)` | Choices: `yes`, `no`, `any` | Preferred smoking habit |
| `pref_sleep` | `CharField(16)` | Choices: `early_bird`, `night_owl`, `flexible` | Preferred sleep schedule |
| `pref_occupation` | `JSONField` | Default `list` | Occupations allowed (`student`, `private_job`, etc. or `any`) |
| `created_at` | `DateTimeField` | `auto_now_add=True`, `db_index=True` | Feed recency ordering key |
| `archived_at` | `DateTimeField` | Nullable, blank, `db_index=True` | Stamped when > 60 days old |
| `withdrawn_at` | `DateTimeField` | Nullable, blank, `db_index=True` | Stamped when author exits post |

**Indexes**:
- `Index(fields=['author', 'archived_at', 'withdrawn_at'], name='listing_author_active_idx')` for 3-active cap check.
- `Index(fields=['-created_at'], name='listing_feed_recency_idx')` for feed sorting.

### 2. `ListingPhoto` Model (`apps.listings.models.ListingPhoto`)

| Column | Type | Constraints & Attributes | Description |
|---|---|---|---|
| `id` | `UUIDField` | Primary Key, default `uuid.uuid4`, editable=False | Unique photo identifier |
| `listing` | `ForeignKey` | `Listing`, `on_delete=models.CASCADE`, `related_name="photos"` | Parent listing container |
| `photo_path` | `CharField(255)` | Relative path within `media/` | Location on disk |
| `order` | `PositiveSmallInteger` | Range `0` to `6`, `default=0` | Display ordering sequence |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Timestamp uploaded |

---

## Service Contracts & Methods

### 1. `ListingService.create()`

```python
@classmethod
def create(
    cls,
    author: Passport,
    *,
    kind: str,
    rent_bdt: int,
    rent_unit: str,
    area: list[str],
    body: str | None = None,
    pref_gender: str,
    pref_smoking: str,
    pref_sleep: str,
    pref_occupation: list[str],
    photo_files: list[Any],
) -> dict[str, Any]:
    """
    Creates a new listing enforcing verified author, cross-field parity,
    atomic 3-active cap check, photo validation, and audit trail logging.
    """
```

**Execution Steps**:
1. Check `author.status == Passport.Status.VERIFIED`. Return `{ok: False, code: "unverified_author"}` if false.
2. Inside `transaction.atomic()`:
   - Query `Listing.objects.select_for_update().filter(author=author, archived_at__isnull=True, withdrawn_at__isnull=True).count()`.
   - If count ≥ 3: return `{ok: False, code: "active_cap_reached", message: "..."}`.
   - Validate `kind ↔ rent_unit`: if `kind == 'seat'`, require `rent_unit == 'per_seat'`; if `kind == 'room'`, require `rent_unit == 'per_room'`.
   - Validate `photo_files`: count must be 1 to 7. Call `ListingPhotoStorageService.validate_photo_batch(photo_files)`.
   - Instantiate and save `Listing`.
   - Save photos via `ListingPhotoStorageService.save_photo()` and persist `ListingPhoto` records.
   - Call `AuditService.append(actor_id=author.user.pk, target=listing, action='create', after_state={...})`.
3. Return `{"ok": True, "listing": listing}`.

### 2. `ListingService.edit()`

```python
@classmethod
def edit(
    cls,
    listing: Listing,
    *,
    actor: Any,
    fields: dict[str, Any],
    new_photo_files: list[Any] | None = None,
    delete_photo_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Updates mutable fields while strictly blocking locked fields (kind, area).
    """
```

**Execution Steps**:
1. Check `actor == listing.author.user` or `actor.is_staff`.
2. Check locked fields: if `'kind'` in fields or `'area'` in fields: return `{ok: False, code: "field_locked", message: "Listing kind and area are permanent and cannot be changed."}`.
3. Validate mutable fields: `rent_bdt` (500–50000), `rent_unit` (must match existing `kind`), `body` (≤500 chars).
4. Calculate resulting photo count: `current - len(delete_photo_ids) + len(new_photo_files)`. Enforce `1 <= count <= 7`.
5. Persist updates and emit `AuditService.append(action='edit', ...)`.
6. Return `{"ok": True, "listing": listing}`.

### 3. `ListingService.withdraw()`

```python
@classmethod
def withdraw(cls, listing: Listing, *, actor: Any) -> dict[str, Any]:
    """Manually marks a listing as withdrawn, removing it from active cap."""
```

### 4. `ListingService.archive_stale()`

```python
@classmethod
def archive_stale(cls, cutoff_days: int = 60) -> dict[str, Any]:
    """Auto-archives active listings older than 60 days. Emits audit log entries."""
```

---

## Photo Storage Architecture

### 1. File Path Convention
```text
media/
└── listings/
    └── photos/
        └── <listing_id>/
            ├── photo_<uuid4>.jpg
            └── photo_<uuid4>.png
```

### 2. Security & Validation Rules
- **Magic Byte & Header Inspection**: Inspects binary headers with `PIL.Image.open(file).verify()` to prevent disguised shell scripts or corrupted payloads.
- **Supported Formats**: JPEG, PNG, WebP only.
- **Max File Size**: 5.0 MB per image file.
- **Original Resolution**: Stored at original resolution without forced downscaling or cropping.

---

## Error Handling Matrix

| Failure Condition | Error Code | Response / Feedback |
|---|---|---|
| Author not passport-verified | `unverified_author` | 403 Forbidden / Redirect to passport wizard |
| Author has 3 active listings | `active_cap_reached` | Form error: "Active listing limit reached (3/3)" |
| Kind is `seat` but rent_unit is `per_room` | `invalid_rent_unit` | Field error: "Rent unit for a seat must be per_seat" |
| Rent outside [৳500, ৳50,000] | `invalid_rent_amount` | Field error: "Rent must be between ৳500 and ৳50,000" |
| Attempting to edit `kind` or `area` | `field_locked` | Error: "Accommodation kind and area cannot be altered post-publish" |
| Uploading 0 or > 7 photos | `invalid_photo_count` | Error: "Please upload between 1 and 7 photos" |
| Uploading file > 5MB | `file_too_large` | Error: "Photo exceeds maximum allowed size of 5 MB" |
| Non-author attempting edit/withdraw | `forbidden_actor` | 403 Forbidden |
