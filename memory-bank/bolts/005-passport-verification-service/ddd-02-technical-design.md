---
unit: 001-passport-and-verification-domain
bolt: 005-passport-verification-service
stage: design
status: complete
updated: '2026-10-30T17:50:00Z'
---

# Technical Design: 001-passport-and-verification-domain

## Architecture Pattern

**Domain-Driven Layered Architecture with Service Spine (AD-1, AD-2, AD-4, AD-9, AD-10, AD-15)**:
The Passport and Verification domain is partitioned across three focused applications:
- `apps.passports`: Passport aggregate and Lifestyle Profile entities with post-verification immutability.
- `apps.verification`: Verification attempt entity, private PII filesystem storage, canonical reject reasons enum, Django admin FIFO queue with authenticated document streaming, and `VerificationService` as the sole state mutator.
- `apps.audit`: Append-only transactional audit trail (`AuditEntry`) recording all state mutations.

## Layer Structure

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Presentation & Admin Layer                                             │
│ - apps/verification/admin.py: Django Admin FIFO Queue & Review actions │
│ - apps/verification/views.py: Staff-only Private Media Stream View    │
├────────────────────────────────────────────────────────────────────────┤
│ Service / Application Layer                                            │
│ - apps/verification/services/verification_service.py: Sole mutator     │
│ - apps/verification/services/storage.py: Private storage backend       │
│ - apps/audit/services/audit_service.py: Append-only compliance log      │
├────────────────────────────────────────────────────────────────────────┤
│ Domain Layer                                                           │
│ - apps/verification/services/reject_reasons.py: 5-member canonical enum│
│ - apps/passports/validators.py: Dhaka areas & budget range validators │
├────────────────────────────────────────────────────────────────────────┤
│ Infrastructure & Persistence Layer                                     │
│ - apps/passports/models.py: Passport & LifestyleProfile (UUID4 PK)     │
│ - apps/verification/models.py: Verification attempt (UUID4 PK)         │
│ - apps/audit/models.py: AuditEntry (UUID4 PK, append-only)             │
│ - media_private/: Isolated filesystem root (AD-9)                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Private PII Storage & Admin Preview Architecture

### 1. Filesystem Isolation (AD-9)
```text
project_root/
├── media/                 # Public media (e.g. listing photos) - exposed via MEDIA_URL
└── media_private/         # Isolated private documents - ZERO public URL mapping
    └── verifications/
        └── <passport_id>/
            ├── nid_front_<uuid>.jpg
            ├── nid_back_<uuid>.jpg
            └── selfie_<uuid>.jpg
```
- In `config/settings/base.py`:
  ```python
  MEDIA_PRIVATE_ROOT = BASE_DIR / "media_private"
  ```
- No URL pattern in `urls.py` or `urls_public.py` maps `media_private/` to direct HTTP requests.

### 2. Staff-Only Streaming Endpoint
- **URL**: `/admin/verification/media/<uuid:verification_id>/<str:doc_type>/`
- **View**: `PrivateDocumentStreamView`
- **Protection**: `@staff_member_required` (`user.is_authenticated and user.is_staff`).
- **Behavior**:
  1. Verifies staff credentials (redirects non-staff or returns 403).
  2. Retrieves `Verification` by `verification_id`.
  3. Maps `doc_type` (`nid_front`, `nid_back`, `selfie`) to model field.
  4. Resolves absolute path inside `settings.MEDIA_PRIVATE_ROOT`.
  5. Validates file existence on disk (returns 404 if missing).
  6. Returns `FileResponse(open(path, 'rb'), content_type=guessed_mime)`.

### 3. Django Admin Preview Integration
In `apps/verification/admin.py`:
```python
def nid_front_preview(self, obj):
  if obj.nid_front_path:
    url = reverse(
        "admin:verification_private_media",
        args=[obj.id, "nid_front"],
    )
    return format_html(
        '<a href="{0}" target="_blank"><img src="{0}" style="max-height: 200px;'
        ' border-radius: 6px;" /></a>',
        url,
    )
  return "-"
```

---

## Service Contracts (In-Process Interface)

### 1. `VerificationService.submit_verification`
```python
def submit_verification(
    *,
    passport: Passport,
    actor: User,
    nid_front_file: UploadedFile,
    nid_back_file: UploadedFile,
    selfie_file: UploadedFile,
) -> dict[str, Any]:
  """Validates files, enforces cooldown, stores images in media_private/,

  creates Verification in 'submitted' state, marks passport 'pending', and logs
  audit entry.

  Returns:
      {'ok': True, 'verification': Verification} or {'ok': False, 'code':
      'cooldown_active' | 'invalid_files' | 'forbidden_role', 'message': str,
      'remaining_seconds': int (optional)}
  """
```

### 2. `VerificationService.transition` (AD-2 Sole Mutator)
```python
def transition(
    *,
    verification: Verification,
    new_state: str,
    actor: User,
    reason: RejectReason | str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
  """Sole mutator for verification state machine. Enforces role authz

  (is_staff=True required for reviewing/verified/rejected), legal DAG
  transitions, reason enum validation, updates passport status, logs AuditEntry,
  and dispatches status email.

  Returns:
      {'ok': True, 'verification': Verification} or {'ok': False, 'code':
      'forbidden_role' | 'invalid_transition' | 'missing_reason_code',
      'message': str}
  """
```

### 3. `VerificationService.check_cooldown` (FR-9)
```python
def check_cooldown(passport: Passport) -> dict[str, Any]:
  """Checks if passport is under 24-hour rejection cooldown.

  Returns:
      {
          'cooldown_active': bool,
          'remaining_seconds': int,
          'cooldown_until': datetime | None
      }
  """
```

### 4. `AuditService.append` (AD-15)
```python
def append(
    *,
    actor: User,
    target: Model,
    action: str,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
    reason_code: str | None = None,
) -> AuditEntry:
  """Appends an immutable audit entry within the current database transaction."""
```

---

## Data Models & Persistence

### 1. `apps/passports/models.py`
```python
class Passport(models.Model):

  class Status(models.TextChoices):
    UNVERIFIED = 'unverified', 'Unverified'
    PENDING = 'pending', 'Pending Verification'
    VERIFIED = 'verified', 'Verified'
    REJECTED = 'rejected', 'Rejected'

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.OneToOneField(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name='passport',
  )
  display_name = models.CharField(max_length=32, unique=True)
  status = models.CharField(
      max_length=16,
      choices=Status.choices,
      default=Status.UNVERIFIED,
      db_index=True,
  )
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)


class LifestyleProfile(models.Model):

  class Gender(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'

  class Occupation(models.TextChoices):
    STUDENT = 'student', 'Student'
    GARMENTS_WORKER = 'garments_worker', 'Garments Worker'
    PRIVATE_JOB = 'private_job', 'Private Job'
    FREELANCER = 'freelancer', 'Freelancer'
    OTHER = 'other', 'Other'

  class Smoking(models.TextChoices):
    YES = 'yes', 'Yes'
    NO = 'no', 'No'
    OCCASIONALLY = 'occasionally', 'Occasionally'

  class SleepSchedule(models.TextChoices):
    EARLY_BIRD = 'early_bird', 'Early Bird'
    NIGHT_OWL = 'night_owl', 'Night Owl'
    FLEXIBLE = 'flexible', 'Flexible'

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  passport = models.OneToOneField(
      Passport, on_delete=models.CASCADE, related_name='lifestyle_profile'
  )
  gender = models.CharField(max_length=16, choices=Gender.choices)
  occupation = models.CharField(max_length=32, choices=Occupation.choices)
  smoking = models.CharField(max_length=16, choices=Smoking.choices)
  sleep_schedule = models.CharField(
      max_length=16, choices=SleepSchedule.choices
  )
  area_preference = models.JSONField(default=list)  # 13 canonical Dhaka areas
  budget_min = models.PositiveIntegerField()  # ৳500 - ৳50,000
  budget_max = models.PositiveIntegerField()  # ৳500 - ৳50,000
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
```

### 2. `apps/verification/models.py`
```python
class RejectReason(models.TextChoices):
  EXPIRED = 'expired', 'Document Expired'
  MISMATCH = 'mismatch', 'Information Mismatch'
  ILLEGIBLE = 'illegible', 'Illegible Image'
  TAMPERING_SUSPECTED = 'tampering_suspected', 'Tampering Suspected'
  OTHER = 'other', 'Other'


class Verification(models.Model):

  class State(models.TextChoices):
    SUBMITTED = 'submitted', 'Submitted'
    REVIEWING = 'reviewing', 'Reviewing'
    VERIFIED = 'verified', 'Verified'
    REJECTED = 'rejected', 'Rejected'

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  passport = models.ForeignKey(
      'passports.Passport',
      on_delete=models.CASCADE,
      related_name='verifications',
  )
  state = models.CharField(
      max_length=16,
      choices=State.choices,
      default=State.SUBMITTED,
      db_index=True,
  )
  nid_front_path = models.CharField(max_length=255)
  nid_back_path = models.CharField(max_length=255)
  selfie_path = models.CharField(max_length=255)
  reject_reason = models.CharField(
      max_length=32, choices=RejectReason.choices, null=True, blank=True
  )
  reviewer_notes = models.TextField(null=True, blank=True)
  submitted_at = models.DateTimeField(db_index=True)
  last_rejection_at = models.DateTimeField(null=True, blank=True)
  reviewed_by = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name='reviewed_verifications',
  )
  reviewed_at = models.DateTimeField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['submitted_at']  # FIFO queue by default
```

### 3. `apps/audit/models.py`
```python
class AuditEntry(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  actor_id = models.UUIDField(db_index=True)
  target_type = models.CharField(max_length=64, db_index=True)
  target_id = models.UUIDField(db_index=True)
  action = models.CharField(max_length=32)
  before_state = models.JSONField(default=dict)
  after_state = models.JSONField(default=dict)
  reason_code = models.CharField(max_length=32, null=True, blank=True)
  timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

  class Meta:
    ordering = ['-timestamp']
    verbose_name_plural = 'Audit entries'
```

---

## Security Design

| Concern | Approach |
|---------|----------|
| PII Document Exposure | Documents stored in `media_private/` with no direct public route. Staff access only via `@staff_member_required` stream view. |
| Unauthorized Approval | `VerificationService.transition` verifies `actor.is_staff is True` on every approval or rejection. Non-staff calls are rejected with `forbidden_role`. |
| Cooldown Tampering | Cooldown is server-enforced via `timezone.now() - verification.last_rejection_at >= 24h` inside `VerificationService`. Client timestamps have zero effect. |
| Tamper-Proof Audit | `AuditEntry` is write-once (append-only) in the same database transaction as the state transition. |

---

## NFR Implementation

| Requirement | Design Approach |
|-------------|-----------------|
| FIFO Queue Performance | Index on `(state, submitted_at)`. Django Admin changelist queries pending items ordered by `submitted_at ASC` with p95 < 100ms. |
| File Upload Limits | `VerificationStorageService` checks MIME type (`image/jpeg`, `image/png`, `image/webp`) and restricts file size to 5 MB per file. |
| Transactional Atomicity | All state updates (`verification.state`, `passport.status`, `audit_entry`) wrapped in `transaction.atomic()`. |
| Status Email Delivery | Triggered synchronously in test/dev and within 5 minutes of review decision. |
