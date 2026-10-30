---
unit: 001-account-identity-service
bolt: 003-account-identity-service
stage: design
status: complete
updated: '2026-10-30T11:00:00Z'
---

# Technical Design - 001-account-identity-service

## Architecture Pattern

**Domain-Driven Layered Architecture with Service Spine (Architecture Spine AD-1, AD-8)**:
The `apps.accounts` app implements an explicit Service Layer (`AccountService`) positioned cleanly between presentation views and Django ORM models. The service layer is the sole orchestrator of state transitions for user registration, token generation, cryptographic validation, and resend rate-limiting. It returns structured result envelopes (`{ok: bool, ...}`) rather than throwing domain-rule exceptions.

## Layer Structure

```text
┌─────────────────────────────────────────────────────────────┐
│ Presentation Layer (apps/accounts/views/, config/urls_*.py)  │
│ - Thin HTTP views, form binding, HTMX partial rendering      │
├─────────────────────────────────────────────────────────────┤
│ Service / Application Layer (apps/accounts/services/)        │
│ - AccountService (registration, OTP verification, resend)   │
│ - Result envelopes: {ok: bool, value, code, message}        │
├─────────────────────────────────────────────────────────────┤
│ Domain / Security Layer (apps/accounts/validators.py, etc.)  │
│ - PasswordComplexityValidator (5 mandatory rule checks)     │
│ - CaseInsensitiveModelBackend (auth normalization)          │
│ - Cryptographic token generator & SHA-256 hasher            │
├─────────────────────────────────────────────────────────────┤
│ Infrastructure & Persistence Layer (apps/accounts/models.py) │
│ - User (AbstractBaseUser, PermissionsMixin, UUID4 PK)       │
│ - EmailVerificationToken (UUID4 PK, hashed token, cascade)  │
│ - UserManager (case-insensitive query & creation helpers)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Service API Contracts (In-Process Interface)

The presentation layer interacts with `AccountService` using these programmatic signatures:

### 1. `register_user`
```python
def register_user(
    *, email: str, password: str, display_name: str
) -> dict[str, Any]:
    """
    Validates input, creates unverified User, issues initial 6-digit OTP,
    and sends transactional verification email.
    
    Returns:
        {
            'ok': True,
            'user': User,
            'token_id': UUID,
            'raw_token': str,  # only exposed for immediate email / testing
        }
        or
        {
            'ok': False,
            'code': 'email_already_registered' | 'password_too_weak' | 'invalid_display_name',
            'message': str,
            'errors': list[str]
        }
    """
```

### 2. `verify_email_token`
```python
def verify_email_token(
    *, user: User, submitted_code: str
) -> dict[str, Any]:
    """
    Validates submitted 6-digit OTP code against user's latest unconsumed token.
    Uses secrets.compare_digest on SHA-256 hashes.
    
    Returns:
        {
            'ok': True,
            'user': User,
            'message': 'Email successfully verified'
        }
        or
        {
            'ok': False,
            'code': 'token_expired' | 'token_invalid' | 'no_active_token',
            'message': str
        }
    """
```

### 3. `resend_verification_token`
```python
def resend_verification_token(
    *, user: User
) -> dict[str, Any]:
    """
    Checks resend_count < 3. If allowed: invalidates prior tokens,
    generates fresh OTP, increments resend_count, and dispatches email.
    
    Returns:
        {
            'ok': True,
            'attempts_left': int,  # 3 - new_resend_count
            'expires_in_seconds': 300
        }
        or
        {
            'ok': False,
            'code': 'resend_limit_exceeded',
            'message': 'Maximum resend attempts reached. Please restart signup.',
            'attempts_left': 0
        }
    """
```

---

## Data Persistence & Schema Design

### 1. Table `accounts_user` (`AUTH_USER_MODEL`)

```sql
CREATE TABLE accounts_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMPTZ NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    email VARCHAR(254) UNIQUE NOT NULL,
    display_name VARCHAR(32) NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX accounts_user_email_idx ON accounts_user (email);
```

### 2. Table `accounts_emailverificationtoken`

```sql
CREATE TABLE accounts_emailverificationtoken (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ NULL,
    resend_count SMALLINT NOT NULL DEFAULT 0
);

CREATE INDEX accounts_evt_user_created_idx ON accounts_emailverificationtoken (user_id, created_at DESC);
CREATE INDEX accounts_evt_hash_idx ON accounts_emailverificationtoken (token_hash);
```

---

## Security Design

| Concern | Implementation Approach |
|---------|-------------------------|
| **Password Storage** | Django default PBKDF2 with SHA-256 (390,000 iterations) or Argon2id; passwords never stored or logged in plain text. |
| **Password Complexity** | `PasswordComplexityValidator` enforcing: (1) min 8 chars, (2) upper `[A-Z]`, (3) lower `[a-z]`, (4) digit `[0-9]`, (5) symbol `[!@#$%^&*(),.?":{}|<>]`. |
| **OTP Generation** | `secrets.randbelow(900000) + 100000` producing cryptographically strong 6-digit integers (`100000` to `999999`). |
| **OTP Storage** | Stored strictly as `hashlib.sha256(raw_otp.encode('utf-8')).hexdigest()`. Raw OTP exists only in memory during dispatch. |
| **Timing Attacks** | `secrets.compare_digest(stored_hash, submitted_hash)` ensures constant-time comparison. |
| **Brute Force & Flooding** | Bounded 5-minute lifespan (`expires_at`), single-use constraint (`consumed_at`), and hard cap of 3 resends per signup attempt. |
| **Authentication Normalization** | `CaseInsensitiveModelBackend` ensures `User@Domain.com` authenticates identical to `user@domain.com`. |
| **Session Hardening** | `SESSION_COOKIE_AGE = 2592000` (30 days), `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`. |

---

## NFR Implementation

| Requirement | Design Approach |
|-------------|-----------------|
| **Performance (<200ms p95)** | Database queries target indexed UUID4 and unique email columns; SHA-256 token hashing runs in <1ms; async/transaction-safe email dispatch via `transaction.on_commit`. |
| **Scalability** | Single-table User model with cascade deletion; token table queries filter by indexed `user_id` and latest timestamp, avoiding full-table scans. |
| **Reliability** | Decoupled email backend: `django.core.mail.backends.locmem.EmailBackend` in tests, configurable SMTP backend in production. |

---

## Error Handling & Service Codes

| Scenario | Service Code | User-Facing Message | HTTP Status |
|----------|--------------|---------------------|-------------|
| Duplicate Email | `email_already_registered` | "An account with this email already exists." | 400 / Form Error |
| Weak Password | `password_too_weak` | Details of missing character classes | 400 / Form Error |
| Invalid Display Name | `invalid_display_name` | "Display name must be between 2 and 32 characters and contain only valid letters, numbers, and basic punctuation." | 400 / Form Error |
| Expired Token | `token_expired` | "Verification code has expired (5-minute limit). Please request a new code." | 400 / Partial Error |
| Invalid Token | `token_invalid` | "Invalid verification code. Please check and try again." | 400 / Partial Error |
| Resend Cap Exceeded | `resend_limit_exceeded` | "Maximum resend attempts reached. Please restart signup." | 429 / Warning |

---

## External Integrations

| Dependency | Purpose | Integration Pattern |
|------------|---------|---------------------|
| **Django Email Backend** | Outbound transactional emails (OTP codes) | `send_mail` via Django SMTP backend (or in-memory in dev/test) using templates in `templates/accounts/email/`. |
| **Django Admin** | Staff management of user records | `UserAdmin` subclass in `apps/accounts/admin.py` with custom search and fieldsets. |
