---
bolt: 007-listing-domain-service
created: '2026-10-31T08:00:00Z'
status: accepted
superseded_by: null
---

# ADR-003: Public Listing Media Architecture and Active-Cap Concurrency Control

## Context

In Basha Pass, accommodation listings represent supply-side inventory created by verified tenants. Implementing the listing domain requires addressing three distinct technical challenges:
1. **Photo Storage & Security**: Unlike citizen identity documents (NIDs) which are confidential PII requiring `media_private/` isolation (ADR-002), listing photos are public marketing images that will be browsed by thousands of seekers on the feed. However, accepting user-uploaded images introduces risks of malicious executable uploads, oversized files, and storage exhaustion.
2. **Active-Cap Concurrency Invariant (FR-12, AD-6)**: A verified tenant is strictly limited to 3 active listings (`archived_at IS NULL AND withdrawn_at IS NULL`). If a tenant submits concurrent requests (e.g., dual browser tabs or network retries), a standard `.count()` check creates a race condition that could violate the 3-listing cap.
3. **Multi-Select Array Storage Portability**: Listings require multi-selection of 1 to 13 Dhaka sub-areas and preferred occupations. While PostgreSQL supports `ArrayField`, SQLite (used for lightning-fast pytest test execution) lacks native array column types.

---

## Decision

### 1. Public Media Storage with Pillow Payload Verification
- Listing photos are stored in the public media directory under `media/listings/photos/<listing_id>/<uuid>.<ext>`, served via standard `MEDIA_URL`.
- Before persisting, `ListingPhotoStorageService` inspects the byte payload using `PIL.Image.open(file).verify()`, validates MIME type (`image/jpeg`, `image/png`, `image/webp`), enforces a maximum size of 5.0 MB per file, and bounds photo counts to between 1 and 7 photos per listing.
- Files are saved at original upload resolution (no client or server-side downscaling/cropping) per PRD FR-10.

### 2. Pessimistic Row Locking for 3-Active Cap Concurrency
- In `ListingService.create()`, the active-cap check executes within an explicit `transaction.atomic()` block.
- The service acquires a pessimistic row lock on the author's `Passport` record via `Passport.objects.select_for_update().get(id=author.id)`.
- Because all creation attempts for a tenant must acquire this lock, concurrent creation transactions are serialized. The active listing count (`Listing.objects.filter(author=author, archived_at__isnull=True, withdrawn_at__isnull=True).count()`) is evaluated with guaranteed isolation, making it impossible to exceed the 3-active listing limit.

### 3. Portable JSONField with Canonical Domain Validation
- Both `area` and `pref_occupation` are implemented as `models.JSONField(default=list)`.
- Model and form validation enforce that `area` is a non-empty subset of the 13 canonical Dhaka sub-areas (reusing `validate_dhaka_sub_areas`), and `pref_occupation` contains only valid occupation choices.
- This maintains 100% test suite compatibility with SQLite while providing full JSON indexing capabilities on PostgreSQL in production.

---

## Rationale

### Alternatives Considered

| Dimension | Alternative Considered | Selected Approach | Rationale for Choice |
|---|---|---|---|
| **Photo Storage** | Private streaming via Django views | Public media storage under `MEDIA_ROOT` | Listing photos are public assets intended for high-throughput listing feed viewing; streaming them through Django views would create unnecessary CPU and memory bottlenecks. |
| **Active Cap Concurrency** | Optimistic locking / Celery queue | Pessimistic `select_for_update()` on `Passport` | Eliminates race conditions with zero external queue dependencies. Since listing creation is an infrequent user action, lock contention is practically zero. |
| **Array Storage** | PostgreSQL-only `django.contrib.postgres.fields.ArrayField` | Standard `models.JSONField` with domain validators | `ArrayField` breaks SQLite test runners. `JSONField` works seamlessly across all database backends while maintaining strict type validation. |

---

## Consequences

### Positive
- **Guaranteed Invariant**: Impossible for any tenant to exceed the 3-active listing limit, even under intentional concurrent bombardment.
- **Fast Media Delivery**: Listing photos can be served directly by Nginx / CDN without hitting Python worker processes.
- **Secure Uploads**: Pillow verification prevents arbitrary file upload (AFU) vulnerabilities, polyglot files, and corrupted binaries.
- **Developer Velocity**: Test suite runs against in-memory SQLite in < 2 seconds without requiring PostgreSQL container dependencies during unit test cycles.

### Negative / Trade-offs
- `select_for_update()` locks the `Passport` row briefly during listing creation (mitigated because transactions complete in < 50ms).
- Uploading photos consumes disk space in `MEDIA_ROOT` (mitigated by hard 5MB limit and 7-photo max cap).

---

## Related
- **Stories**: `017-listing-and-photo-models`, `018-listing-service-and-active-cap`, `019-listing-photo-storage-service`
- **Architecture Spine**: `AD-6` (ListingService invariants), `AD-9` (Storage architecture), `AD-15` (Audit trail)
- **Previous ADRs**: `ADR-002` (Private PII Media Storage for Identity Verification)
