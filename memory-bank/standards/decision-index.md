---
last_updated: '2026-10-30T17:55:00Z'
total_decisions: 2
---

# Decision Index

This index tracks all Architecture Decision Records (ADRs) created during Construction bolts.
Use this to find relevant prior decisions when working on related features.

## How to Use

**For Agents**: Scan the "Read when" fields below to identify decisions relevant to your current task. Before implementing new features, check if existing ADRs constrain or guide your approach. Load the full ADR for matching entries.

**For Humans**: Browse decisions chronologically or search for keywords. Each entry links to the full ADR with complete context, alternatives considered, and consequences.

---

## Decisions

### ADR-001: Store 6-Digit Email Verification Tokens as SHA-256 Hashes
- **Status**: accepted
- **Date**: 2026-10-30
- **Bolt**: `003-account-identity-service` (`001-account-identity-service`)
- **Path**: [`bolts/003-account-identity-service/adr-001-hashed-email-otp-storage.md`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/bolts/003-account-identity-service/adr-001-hashed-email-otp-storage.md)
- **Summary**: Basha Pass requires tenants to verify their email address during signup by submitting a 6-digit numeric OTP token. We will store only the SHA-256 hex digest of the OTP in the database, verifying incoming submissions via constant-time comparison.
- **Read when**: Implementing or modifying token generation, email verification, password reset, or OTP handling across identity and auth services.

### ADR-002: Private PII Media Storage with Staff-Only Authenticated Streaming
- **Status**: accepted
- **Date**: 2026-10-30
- **Bolt**: `005-passport-verification-service` (`001-passport-and-verification-domain`)
- **Path**: [`bolts/005-passport-verification-service/adr-002-private-pii-media-storage-and-staff-streaming.md`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/bolts/005-passport-verification-service/adr-002-private-pii-media-storage-and-staff-streaming.md)
- **Summary**: Tenants upload sensitive identity documents (NID front/back and selfie) for verification. We isolate documents under `media_private/` with no direct public route, serving previews exclusively through a staff-authenticated Django streaming view.
- **Read when**: Storing or serving sensitive citizen PII documents, handling file uploads in verification or user profile flows, or configuring admin document previews.
