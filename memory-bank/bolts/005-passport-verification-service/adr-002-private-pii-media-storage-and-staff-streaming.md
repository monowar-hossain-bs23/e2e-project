---
bolt: 005-passport-verification-service
created: '2026-10-30T17:55:00Z'
status: accepted
superseded_by: null
---

# ADR-002: Private PII Media Storage with Staff-Only Authenticated Streaming

## Context

In Basha Pass, tenants submit National ID (NID front and back) and a selfie holding the NID for identity verification. Standard Django configurations store user uploads under `MEDIA_ROOT` (`/media/...`), which are served statically by web servers or Django's static handler to anyone possessing the URL without authentication.

Treating citizen identity documents as public media poses severe privacy and security risks:
- Web crawlers, search engines, or malicious third parties could scrape citizen identity cards.
- Tenants or competitors could enumerate or guess document URLs to harvest personal data.
- Public browser caches or CDN nodes could cache sensitive identity documents.

However, internal verification staff still need to view high-resolution previews and thumbnails of these documents directly within the Django Admin FIFO review queue.

## Decision

We will isolate all verification identity documents in a dedicated private directory: `media_private/` (`MEDIA_PRIVATE_ROOT = BASE_DIR / "media_private"`), managed by `VerificationStorageService`.
- No public URL route will map to `media_private/`.
- Document previews will be served exclusively through an internal, staff-authenticated streaming view:
  ```text
  /admin/verification/media/<uuid:verification_id>/<str:doc_type>/
  ```
- This view enforces `@staff_member_required` (`user.is_authenticated and user.is_staff`) and returns an authenticated `FileResponse`.
- The Django Admin `VerificationAdmin` review screen will embed secure `<img>` tags referencing this streaming route.

## Rationale

This approach provides defense-in-depth:
1. **Access Isolation**: Non-staff users and anonymous visitors cannot access files, even if they know the UUID.
2. **Path Traversal Protection**: The view resolves paths strictly within `MEDIA_PRIVATE_ROOT` using relative subpaths and fixed document discriminators (`nid_front`, `nid_back`, `selfie`).
3. **Operational Simplicity**: No external cloud S3/GCS bucket setup or signed URL infrastructure is required for the v1 MVP, while the abstract `VerificationStorageService` allows transparent migration to object storage in v2.

### Alternatives Considered

| Alternative | Pros | Cons | Why Rejected |
|-------------|------|------|--------------|
| **Public MEDIA_ROOT with Random UUIDs** | Simple to render in admin | Zero access control; URLs can leak via referrers or browser history | Violates PII privacy and PRD §4.2 / AD-9 standards |
| **Signed S3 Cloud URLs** | Offloads streaming from Django | Requires cloud provider setup, AWS credentials, and presigned URL lifecycles | Unnecessary operational complexity for single-server v1 MVP |
| **Base64 in Database (BYTEA / Text)** | No separate filesystem concerns | Bloats database tables and backups; slows query latency on 5 MB photos | Poor scalability and inefficient memory usage |
| **Private Filesystem + Staff Streaming View (Selected)** | True access control, zero public routes, native Django admin preview | Streams file through Django process | Acceptable overhead since review queue traffic is low-frequency internal staff volume |

## Consequences

### Positive
- Strict PII isolation: citizen identity documents are completely shielded from public web access.
- Staff can seamlessly inspect full-size documents and thumbnails in Django Admin.
- Unauthenticated or non-staff requests immediately receive 403 Forbidden or redirect to login.

### Negative
- Serving media through Django consumes application worker memory/threads during preview loads (mitigated by low volume of staff reviewers).

### Risks
- High staff queue volume could introduce minor latency during bulk review.
  - *Mitigation*: Thumbnails are scaled in CSS and previews are loaded only when viewing individual submissions.

## Related

- **Stories**: `012-verification-model-and-private-storage`, `014-admin-verification-queue`
- **Architecture Standards**: Architecture Spine AD-9 (`Private PII Storage`), AD-10 (`Admin Surface`)
- **Previous ADRs**: `ADR-001: Store 6-Digit Email Verification Tokens as SHA-256 Hashes`
