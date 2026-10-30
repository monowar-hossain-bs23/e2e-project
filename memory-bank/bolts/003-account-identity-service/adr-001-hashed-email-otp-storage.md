---
bolt: 003-account-identity-service
created: '2026-10-30T11:08:00Z'
status: accepted
superseded_by: null
---

# ADR-001: Store 6-Digit Email Verification Tokens as SHA-256 Hashes

## Context

Basha Pass requires tenants to verify their email address during signup by submitting a 6-digit numeric OTP token. Because email verification tokens grant account activation and session authentication, storing them in plain text in the database exposes users to security risks:
- Database backups, replication streams, or audit dumps could reveal active tokens.
- Internal operators or developers with database read access could inspect tokens.
- Any accidental logging of ORM queries or admin inspection could compromise user verification.

## Decision

We will store only the SHA-256 hex digest (`hashlib.sha256(raw_otp.encode('utf-8')).hexdigest()`) in the `EmailVerificationToken.token_hash` field.
The raw 6-digit OTP will exist exclusively in-memory during token generation and transactional email dispatch. Verification of incoming user submissions will compute the SHA-256 hash of the submitted code and compare it against the stored hash using `secrets.compare_digest` to prevent timing attacks.

## Rationale

SHA-256 is fast, deterministic, cryptographically secure against pre-image attacks, and native to Python's standard library (`hashlib`). Given the 5-minute lifespan and 3-attempt resend cap, precomputing hashes for 900,000 possible 6-digit codes is mitigated by short expiration and single-use invalidation.

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **Plain-Text OTP Storage** | Simpler queries and debugging | Severe security risk; tokens exposed in DB dumps and logs | Fails security and least-privilege standards |
| **PBKDF2 / Argon2id Hashing** | Extremely high work factor against brute-force | Excessive CPU latency for high-frequency 5-minute ephemeral tokens | Unnecessary overhead for 5-minute tokens protected by attempt limits |
| **SHA-256 Hashing with Constant-Time Comparison (Selected)** | Zero external dependencies, <1ms computation, protects at rest | 6-digit keyspace is small without salt | Acceptable given strict 5-min expiry and max 3-attempt rate limiting |

## Consequences

### Positive
- Tokens are protected at rest; compromised database dumps cannot be used directly to take over unverified accounts.
- Constant-time verification eliminates side-channel timing attack vectors.
- Aligns with zero-trust credential hygiene.

### Negative
- Support staff cannot retrieve or read a user's verification token directly from the database to assist them (user must use "Resend code").

### Risks
- **Rainbow Table / Pre-image on 6 digits**: A 6-digit numeric OTP has only 900,000 permutations.
  - *Mitigation*: Tokens expire within 5 minutes, are single-use, and are throttled by a hard limit of 3 resends per signup session.

## Related

- **Stories**: `006-email-verification-token-and-service`, `008-signup-and-verify-email-views`
- **Standards**: `memory-bank/standards/system-architecture.md`, `memory-bank/standards/coding-standards.md`
- **Previous ADRs**: None
