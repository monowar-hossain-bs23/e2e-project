---
title: PRD — Basha Pass v1
created: 2026-08-30
updated: 2026-08-30
status: draft
---

# PRD: Basha Pass v1

## 0. Document Purpose

This PRD is the operational specification for **Basha Pass v1** — a verified roommate and seat-matching platform for urban Bangladesh. It builds on the Product Brief at `memory-bank/planning-artifacts/briefs/brief-basha-pass-2026-08-30/brief.md` and its companion `addendum.md`; treat those as the executive narrative and refer here for behavioral requirements.

Audience: the founding team and downstream workflow owners — UX designers, architects, epic/story authors. Structure: a Glossary-anchored vocabulary, Features grouped with FRs nested under each (globally numbered FR-1 through FR-N for stable references), User Journeys as named-persona narratives with stable IDs (UJ-1 through UJ-N), and inline `[ASSUMPTION]` tags indexed in §9. Unknowns are tracked in §8 Open Questions, not papered over. Most `[ASSUMPTION]` rows have been resolved through PRD review (see §9); remaining assumptions are now limited to seed values, capacity monitoring, and a small number of operational NFRs.

Stakes: internal / pre-launch. Length target ~5–8 pages.

## 1. Vision

Basha Pass replaces two pains every urban Bangladesh renter feels on every move: the **search grind** (walking streets, calling handwritten To-Let signs, visiting empty apartments) and the **paperwork grind** (surrendering NID + photos to a new landlord for police verification, every time). v1 is a **verified supply-side discovery product**: verified tenants list a seat in a mess or a room for rent; other tenants browse, filter, view contact info, and reach out off-platform. Once a tenant verifies their identity with Basha Pass once, they carry a **Tenant Passport** — a portable, NID-verified credential that travels across rentals, eliminating the need to re-share sensitive identity documents with every new person they meet.

The product is built first for Dhaka — but the architecture is city-agnostic from day one, so that second-city rollout becomes configuration, not rebuild. v1 is free, ships as a responsive web app, and intentionally does **not** include in-app chat, contact-share handshakes, match-closure flows, post-match surveys, in-app reports, or admin moderation queues. Verified seekers view lister contact information directly on the Listing detail page and reach out off-platform through their preferred channel — the natural Bangladesh pattern. v1 is also intentionally **not** a landlord/mess-owner dedicated product; the wedge in v1 is verified tenants who are also current renters, and the lister surface is one mode of the same tenant account.

The honest framing: this is a passion project with a real, addressable market. v1's job is to learn whether the Tenant Passport concept has legs in one city. If it does, the vision justifies itself and the product expands from tenant-to-tenant matching into the broader rental and identity ecosystem. If it does not, the brief and PRD are worth having written because they tell us why — and we move on with that knowledge.

## 2. Target User

### 2.1 Jobs To Be Done

**Functional**
- Find a compatible roommate or a seat in a mess/sublet/bachelor pad without street-walking or cold-calling To-Let signs
- Avoid scams and unverifiable listings
- Verify identity once and reuse that verification across many rental contexts
- Get matched on dimensions that actually predict compatibility (sleep schedule, smoking, occupation, area, budget)

**Emotional**
- Reduce the anxiety of handing NID copies to strangers
- Reduce the loneliness and friction of arriving in a new city with no network
- Feel "checked" — that the person on the other side of the match has been verified by a trusted third party

**Social**
- Match with people of similar background (student with student, garments worker with garments worker)
- Maintain appropriate gender separation where culturally required (default to same-gender matching, explicit override)

**Contextual**
- Work on a phone with intermittent 3G/4G
- Use English (English-only UI in v1 — Bangla support is v2)
- Move on short timelines (semester start, job start, factory posting)

### 2.2 Non-Users (v1)

- **Dedicated landlord / mess-owner / subletter accounts** — they are not users in v1. The lister in v1 is a current tenant offering a seat or room they occupy, using the same tenant account. A dedicated landlord-facing product is a v2 wedge.
- **Whole-apartment renters** (families, couples, established professionals renting a full unit) — v1 is for the seat/room sub-segment specifically. The "To-Let" walk pain exists for them too, but the discovery mechanics and trust signals differ; they are a v2+ audience.
- **Tenants outside Dhaka** — v1 launches for Dhaka only. Architecture is city-agnostic but the launch is single-city.
- **Anyone unwilling to share an NID photo + selfie** — verification is mandatory. There is no unverified tier.
- **Users seeking an in-app chat, messaging, contact-share handshake, match-closure, or in-app report flow** — v1 explicitly does not provide any of these; tenants reach out off-platform using the contact information visible on Listing detail.

### 2.3 Key User Journeys

**UJ-1. Rimon, the migrating student, finds a compatible mess seat in Dhaka within his first week.**
- **Persona + context:** Rimon, 21, just admitted to a university in Dhaka from a district town. Arrived three days ago. No local network. Needs a seat in a male mess near campus, budget ৳3500–5000, move-in within a week.
- **Entry state:** Not yet a Basha Pass user. Has a phone with intermittent 3G. Has his NID and a selfie on the phone.
- **Path:**
  1. Discovers Basha Pass via a friend or a poster near a coaching center.
  2. Signs up with email + password; verifies email via 6-digit token sent to inbox.
  3. Creates his Tenant Passport: uploads NID front + back, takes a selfie holding the NID, fills the lifestyle profile (gender: male, occupation: student, smoking: no, sleep: early bird, area: near campus, budget: ৳3500–5000).
  4. Submits — sees a "verification pending" status. Returns the next day to a "verified" passport.
  5. Browses the "Looking For" feed filtered to his area. Finds three compatible posts within 24 hours.
  6. Responds to one — "Hi, I'm Rimon, just arrived for university, your post matches my profile, can we chat?"
  7. Match moves to email/phone/WhatsApp within 2 messages (per Basha Pass UI hint after first reply).
  8. Arranges to visit the mess, meets the roommate, decides to move in.
- **Climax:** Within 6 days of arriving in Dhaka, Rimon is moved into a verified mess seat with a compatible roommate. He never had to walk a street looking at To-Let signs.
- **Resolution:** Rimon uses his Tenant Passport for the mess owner's police verification handoff (one tap, no rescanning). Profile stays live for future moves.
- **Edge case:** If Rimon's NID upload is rejected (illegible, expired, mismatch), he gets a clear error message and a retry path with a 24-hour cooldown on resubmits to prevent fraud.

**UJ-3. Sabbir, the young professional, posts a "looking for" and is approached by a compatible match.**
- **Persona + context:** Sabbir, 27, first job in Dhaka, working in Banani. Currently in a temporary mess but wants a more stable 2-bedroom bachelor pad with a compatible roommate. Budget ৳6000–8000/seat, area preference: Banani / Gulshan / Baridhara, move-in within a month.
- **Entry state:** Already a verified Basha Pass user (verified when he first tried the product to find the temporary mess).
- **Path:**
  1. Goes to "Looking For" and posts his own search: "Looking for 1 roommate to share a 2BR in Banani area, ৳7000/seat, male, professional, non-smoker, early bird, move-in by Sept 30."
  2. Within 48 hours, receives 3 responses from other verified tenants. One profile is a strong match (also professional, non-smoker, Banani-based, ৳7500 budget).
  3. They chat briefly in the app, then exchange contact info (email or phone, at their choice), then visit a couple of bachelor pads together, then sign a rental agreement with a landlord.
  4. Sabbir updates his profile to "currently housed" so he no longer surfaces in active-search feeds.
- **Climax:** Two verified tenants find each other, jointly rent a pad, and the landlord receives pre-verified tenant profiles (one tap each) — eliminating the per-tenant NID-photocopy loop.
- **Resolution:** Sabbir's profile is marked as housed. He can reactivate it for his next move.
- **Edge case:** If Sabbir gets no compatible responses after 14 days, the product surfaces a gentle nudge ("Want to broaden your area filter?") to prevent dead-end experiences.

**UJ-4. Basha Pass admin verifies a Tenant Passport submission.**
- **Persona + context:** A member of the Basha Pass team (founder or operator). Reviews pending verifications in the admin queue.
- **Entry state:** Logged into the admin dashboard. Has a queue of 5–50 pending submissions.
- **Path:**
  1. Opens the queue, sees thumbnails of NID + selfie for each pending submission.
  2. Opens one submission. Sees NID front, NID back, selfie, submitted timestamp.
  3. Checks: NID is legible and not expired. Selfie plausibly matches the NID photo. No obvious signs of tampering (cropping, edge artifacts, mismatched lighting).
  4. Approves or rejects with a reason code (`expired`, `mismatch`, `illegible`, `tampering_suspected`, `other`).
  5. Tenant is notified of the decision. Approved tenants go live immediately. Rejected tenants enter a 24-hour cooldown before they can resubmit.
- **Climax:** Admin clears the queue; verified passport goes live; tenant receives push/email notification.
- **Resolution:** Admin moves to the next submission. The audit trail (who approved, when, which reason code) is retained.
- **Edge case:** If the queue exceeds 50 pending submissions, the system alerts the admin (and the founder, if separate) so capacity can be scaled or temporary reviewers added.

**UJ-5. A tenant reports a concerning match for safety review.**
- **Persona + context:** A verified tenant has matched with another verified tenant. After off-platform (email/phone/WhatsApp) contact, something feels off — pressure to share more documents, inappropriate language, or a mismatch between the profile and reality.
- **Entry state:** Inside the Basha Pass web app, viewing the match conversation.
- **Path:**
  1. Taps "Report" on the match.
  2. Selects a reason (`pressure_for_docs`, `inappropriate_language`, `profile_mismatch`, `safety_concern`, `other`).
  3. Adds a free-text note.
  4. Submits. Report enters the admin queue with a "safety" priority flag.
  5. Admin reviews within 24 hours. May suspend the reported tenant's passport pending investigation. Reporter is notified of the resolution.
- **Climax:** Basha Pass acts on the safety signal, protecting future tenants from a pattern.
- **Resolution:** The reported tenant's passport status changes (`active`, `suspended`, `banned`). The audit trail is retained.
- **Edge case:** If the reporter themselves is in immediate physical danger, Basha Pass surfaces crisis-resources information on the report confirmation screen, prominently displaying **Bangladesh National Emergency Service: 999** (RESOLVED 2026-08-30). Additional context-appropriate resources may be added by the PM in v1.x based on user-research findings (e.g., women's-safety, labor-rights hotlines).

## 3. Glossary

- **Tenant** — A renter in urban Bangladesh, specifically a person seeking a seat in a mess, sublet, or bachelor pad. The only first-class user in v1.
- **Tenant Passport** — A verified profile consisting of: an email address (the account identifier), an NID photo (front + back), a selfie, a lifestyle profile, and a verification status (`pending`, `verified`, `rejected`, `suspended`, `banned`). One passport per tenant; portable across rentals.
- **Verification** — The process by which Basha Pass confirms that an uploaded NID + selfie match a real person. In v1, manual review by a Basha Pass admin. Future v2: government or partner-API eKYC.
- **Lifestyle Profile** — Six fields captured at passport creation: gender, occupation, smoking preference, sleep schedule, area preference, budget.
- **Listing** — A supply-side post authored by a verified tenant describing an available seat in a mess or a room for rent. The Listing carries: kind (seat or room), area(s), rent, rent_unit (`per_seat` or `per_room`), rent_period (`per_month`), photos, a body, and the lister's preferences (preferred gender, smoking, sleep, occupation). The core matching surface in v1.
- **Rent unit** — The thing to which the rent amount applies. In v1: `per_seat` or `per_room`. "Per month" is not a rent unit; it is a rent period.
- **Rent period** — The duration over which the rent amount is charged. In v1: `per_month` only — fixed by the platform, not selected by the user.
- **Match** — Reserved for v2. In v1 there is no in-app match state, contact-share handshake, or match-closure flow. Verified seekers browse Listings, view lister contact info, and reach out off-platform.
- **Feed** — The chronological or filtered list of active Listings visible to logged-in tenants. Filterable by area, budget range, kind, rent_unit, gender, occupation, smoking, and sleep schedule.
- **Admin** — A Basha Pass team member with access to the verification queue, reporting queue, and audit trail. In v1, the founder(s).
- **Mess** — A shared living arrangement in Bangladesh, typically with shared kitchen and individual rooms or shared rooms with multiple beds ("seats"). Common for bachelors, students, and garments workers.
- **Seat** — A single bed-space in a mess or sublet. The unit of inventory at the matching layer (tenants match for "seats," not whole apartments).
- **Sublet** — A room or portion of a dwelling rented out by a current tenant (rather than the property owner).
- **Bachelor Pad** — A small apartment (often 1-2 BR) shared by unmarried young men. "Bachelor" here is Bangladesh-cultural shorthand, not a marital-status filter.
- **Police Verification (Thana Verification)** — The legal requirement in Bangladesh for landlords to submit tenant NID copies + photographs to the local police station after a tenant moves in. Basha Pass does not close this loop in v1 — it gives tenants a verified credential they can present to landlords, but the thana submission remains the landlord's responsibility.
- **NID** — Bangladesh National ID card, issued by the government. The standard identity document. Two sides (front and back), photo, signature, and a 13- or 17-digit number.
- **Dhaka** — The launch city for v1. Architecture is city-agnostic; second-city expansion is v2.

## 4. Features

### 4.1 Account & Authentication

**Description:** A tenant creates a Basha Pass account with an email address and password. They receive a 6-digit one-time verification token via email to verify the email at signup. Sessions persist across visits (no re-login on the same device for 30 days). There is no phone number or SMS in v1 — email + password only. The same email cannot create multiple accounts. **Email delivery uses Django SMTP integrated with Gmail SMTP for v1. The 500 emails/day Gmail cap is the v1 design ceiling.**

**Functional Requirements:**

#### FR-1: Email-based signup

A new visitor can sign up with an email address, set a password, and receive a 6-digit one-time verification token via email. The tenant enters the token in the app to verify the email and activate the account. Realizes UJ-1, UJ-2.

**Consequences (testable):**
- Email verification is required before the account becomes active (cannot post, respond, or be visible in the feed before verification)
- **Verification token is exactly 6 digits** (RESOLVED 2026-08-30)
- **Verification token expires after 5 minutes** (RESOLVED 2026-08-30)
- **Verification token is single-use** (cannot be re-used after successful verification)
- **Tenant can request a new token (re-send) up to 3 times per signup attempt**, after which the signup must be restarted (RESOLVED 2026-08-30: 3-attempt cap prevents abuse and email-bombing)
- **Password must be at least 8 characters AND contain at least one uppercase letter, at least one lowercase letter, at least one number, AND at least one special character (all four classes required)** (RESOLVED 2026-08-30)
- Same email cannot create a second account
- Sessions persist for 30 days on the same device without re-auth

#### FR-2: Logout and account deletion

A tenant can log out from any device. A tenant can request account deletion; deletion removes the Tenant Passport and any associated data within 30 days (soft-delete with grace period).

**Consequences (testable):**
- Logout invalidates the session immediately
- Account deletion request triggers a confirmation step and a 30-day grace period before permanent removal

**Out of Scope:** Phone-based signup, social login (Google/Facebook), multi-device session management, SMS-based auth. (Email + password is the v1 method.)

### 4.2 Tenant Passport

**Description:** A tenant creates one Tenant Passport. The passport consists of: email address (from account), NID front photo, NID back photo, selfie holding the NID, six lifestyle fields, and a verification status. **Passport fields are immutable after verification in v1 (RESOLVED 2026-08-30) — edit-after-verify is v2.** This reduces the fraud surface in v1 (no risk of a verified tenant swapping their identity or rewriting their profile to match a new match). The passport is the only object that proves a tenant has been verified.

**Functional Requirements:**

#### FR-3: Passport creation

A verified-account tenant can upload NID front, NID back, and a selfie, fill in the six lifestyle fields, and submit for verification. Submission enters `pending` status. Realizes UJ-1, UJ-2.

**Consequences (testable):**
- All required fields are enforced before submission (no half-filled passports)
- Submission generates a unique passport ID and timestamps
- Tenant sees a "verification pending" status immediately after submission
- **Once verified, passport fields (NID photos, selfie, lifestyle profile, display name) are immutable — no edits allowed via UI or API** (RESOLVED 2026-08-30)
- **Tenant must re-verify (resubmit a new passport) if they need to change any verified field** (RESOLVED 2026-08-30) `[ASSUMPTION: re-verification flow requires a new manual admin review; reuse of prior NID photos NOT permitted — every passport resubmission starts from scratch]`

**Out of Scope:** Editing the lifestyle profile post-verification (v2). Confirmed.

#### FR-4: Lifestyle profile (six fields)

The six fields are: **gender** (male, female, other/prefer not to say), **occupation** (student, garments worker, private job, freelancer, other), **smoking** (yes, no, occasionally), **sleep schedule** (early bird, night owl, flexible), **area preference** (Dhaka sub-areas, multi-select), **budget** (৳ range, slider). All six fields confirmed as the v1 lifestyle profile (RESOLVED 2026-08-30). All fields required.

**Consequences (testable):**
- All six fields must be set before submission is enabled
- **Budget slider range is dynamically computed from the database**: minimum = lowest active Looking-For post budget in the same area-filter; maximum = highest active Looking-For post budget in the same area-filter (RESOLVED 2026-08-30). The slider adapts as new posts are created. `[ASSUMPTION: seeded floor ৳500, seeded ceiling ৳50,000 at launch until natural distribution emerges.]`
- **Area preference options are the canonical Dhaka sub-areas**: Mirpur, Mohammadpur, Uttara, Banani, Gulshan, Baridhara, Bashundhara, Dhanmondi, Ramna, Tejgaon, Gazipur, Narayanganj-adjacent, Other (RESOLVED 2026-08-30).

#### FR-5: Passport visibility to others

Verified tenants can see other verified tenants' passport summary (lifestyle fields + verification status + display name). NID photos and selfies are **not** visible to other tenants — they are visible only to admins for verification purposes. Realizes UJ-3.

**Consequences (testable):**
- Other tenants see: display name, gender, occupation, smoking, sleep, area, budget, verification status (verified ✓)
- Other tenants cannot see: NID photos, selfie, email (until explicitly shared via "Share Contact" flow)

#### FR-6: Display name

Every tenant chooses a display name at passport creation. The display name is the only handle other tenants see. Real names are not exposed.

**Consequences (testable):**
- Display name is required
- Display name length is bounded (3–32 characters, RESOLVED 2026-08-30)
- Display name can be changed post-verification; the prior name is retained in audit

**Out of Scope:** Multiple display names per tenant, display name history visible to others.

### 4.3 Verification

**Description:** Manual admin review of NID + selfie submissions. Admin approves, rejects with a reason code, or escalates. Verified passports go live immediately. Rejected passports enter a 24-hour cooldown before resubmission.

**Functional Requirements:**

#### FR-7: Admin verification queue

An admin can view all pending verification submissions, sorted by submission time (FIFO). Each submission shows: NID front, NID back, selfie, submitted timestamp, the tenant's display name, and the lifestyle profile. Realizes UJ-4.

**Consequences (testable):**
- Queue is sorted FIFO by default
- Each submission is viewable in a dedicated review screen
- The admin can approve, reject (with a reason code), or escalate

#### FR-8: Reason codes for rejection

Rejections require a reason code from a fixed set: `expired`, `mismatch`, `illegible`, `tampering_suspected`, `other`. A free-text note is optional.

**Consequences (testable):**
- All rejections must select a reason code
- Reason code is stored in the audit trail

#### FR-9: Re-submission cooldown

A rejected passport cannot be resubmitted for 24 hours (RESOLVED 2026-08-30). After the cooldown, the tenant can re-upload and re-submit.

**Consequences (testable):**
- Cooldown is enforced server-side
- Tenant is shown the remaining cooldown time

**Out of Scope:** Automated verification (OCR, face match, government API), bulk-approval flows, automated fraud scoring.

### 4.4 Listings

**Description:** A Listing is what a verified tenant posts when they have a seat in a mess or a room to rent. The Listing is the supply-side unit of inventory: it describes the available space (kind, area, rent), the photos, and the renter's preferences (who they are looking for). v1 ships one Listing kind: Listing — no separate "Looking For" demand-side post. Whole flats are out of scope. The Listing detail page surfaces the lister's contact information to verified viewers (soft-gate feed), and unverified viewers see everything except contact info (per the locked-contact panel).

**Functional Requirements:**

#### FR-10: Listing creation

A verified tenant can create a Listing describing an available seat in a mess or a room for rent. Required fields: kind (seat or room), area (multi-select from the 13 canonical Dhaka sub-areas), rent (integer BDT, ৳500–৳50,000), rent_unit (`per_seat` or `per_room`), rent_period (`per_month`, system-fixed), preferred gender (male, female, any), smoking (yes, no, any), sleep schedule (early bird, night owl, flexible), occupation (multi-select: student, garments worker, private job, freelancer, other, any), 1–7 photos, and an optional body note (≤500 characters, Bengali script supported). Realizes UJ-1, UJ-2, UJ-3.

**Consequences (testable):**
- Only verified tenants may create a Listing
- If `kind` is `seat`, then `rent_unit` must be `per_seat`
- If `kind` is `room`, then `rent_unit` must be `per_room`
- `rent_unit` may never be `per_month`; `per_month` is a `rent_period`, not a `rent_unit`
- `rent_period` is fixed to `per_month` in v1; not collected from the user
- Rent must be a positive integer in BDT; minimum ৳500, maximum ৳50,000
- At least 1 photo and at most 7 photos per Listing
- Photos must be JPEG, PNG, or WebP; maximum 5 MB each
- Photos are stored at upload resolution; no client-side or server-side crop
- Body is optional and bounded at 500 characters

#### FR-11: Listing feed display and filtering

The feed displays all active Listings in reverse-chronological order (newest first). Filters: area (multi-select), budget range (slider), kind (seat, room), rent_unit (per_seat, per_room), gender (male, female, any), occupation (multi-select), smoking (yes, no, any), sleep schedule (early bird, night owl, flexible). Additive AND across filter categories; OR within a category. Each card renders: photo, kind discriminator, verified badge, rent, rent_unit, area, lifestyle summary, compatibility hint ("matches X of 6 preferences"), and a "View listing" affordance. Compatibility hint is computed server-side and is the only "matching" signal — no percentage, no star rating, no algorithmic ranking. Realizes UJ-1, UJ-2, UJ-3.

**Consequences (testable):**
- Verified viewers see the full card including the lister's lifestyle summary
- Unverified viewers see rent, area, kind, photo, and verified badge; lifestyle summary is replaced with "Verify to see lifestyle fit"
- Contact info (email, phone) is visible on Listing detail for verified viewers only
- Unverified viewers see a locked-contact panel with "Verify to see contact info. Verification usually takes under 24 hours." and a "Verify your passport" CTA
- A compatibility hint of "matches X of 6 preferences" is rendered; X is an integer 0–6
- When X ≥ 4, the hint text uses success-fg; when X < 4, text-muted

#### FR-12: Active listing limit and archive

A verified tenant may have at most 3 active (non-archived, non-withdrawn) Listings at any time. Listings older than 60 days auto-archive; archived Listings are not deleted — they remain visible in "Your listings" when "Show archived" is enabled.

**Consequences (testable):**
- Creating a 4th active Listing is blocked at the form layer and re-enforced server-side
- Listings older than 60 days are not visible in the default feed
- The author always sees their own listings (active and archived) under "Your listings"

### 4.5 Listing Detail & Off-Platform Contact

**Description:** A verified or unverified viewer opens a Listing to review its full details. Verified viewers can see the lister's contact information (email and phone) and reach out off-platform through their preferred channel. Unverified viewers see the complete Listing except contact information; the contact area is replaced by a verification-gated panel. There is no in-app reply thread, in-app messaging, contact-share handshake, match state, match closure, or post-match survey in v1.

**Functional Requirements:**

#### Contact visibility and off-platform handoff

A verified viewer sees contact information directly on Listing detail. An unverified viewer sees a locked panel. No Basha Pass action records or mediates contact sharing. Once a seeker and lister choose to share contact information, they do so off-platform using the channel both parties prefer.

**Consequences (testable):**
- Verified viewer sees both email and phone on Listing detail
- Unverified viewer sees no contact information anywhere on the page
- Unverified viewer sees "Verify to see contact info. Verification usually takes under 24 hours." and a "Verify your passport" CTA
- No in-app reply/message model or contact-share model exists in v1
- No match state, match closure, or post-match survey exists in v1

**Out of Scope:** In-app chat, first-reply messaging, both-tap contact sharing, contact visibility to unverified viewers, match closure, post-match survey, typing indicators, read receipts, and in-app message attachments.

### 4.6 Trust & Safety

**Description:** v1 has no in-app report flow, no admin-driven suspend/ban action, and no admin moderation queue. Trust in v1 is anchored in NID verification at signup and the verified-badge display on Listings. Any safety or fraud escalation happens off-platform through Basha Pass support channels and is processed manually by the founding team. A report-and-resolve flow is a v2 wedge and is intentionally deferred so v1 can ship a focused discovery and listing product.

**Out of Scope for v1:** in-app report action, report reason codes, admin moderation queue, admin suspend/ban actions, status-change audit from reports, reporter confidentiality, and crisis-hotline surfacing on a report confirmation screen.

### 4.7 Notifications

**Description:** v1 sends transactional email only, for one event: verification status changes. No SMS, no push, no in-app notification list, and no notification of off-platform contact sharing.

**Functional Requirements:**

#### FR-18: Verification status notification

A tenant receives an email when their passport verification status changes (verified, rejected).

**Consequences (testable):**
- Email is sent within 5 minutes of status change
- Rejected email includes the reason code in human-readable form

**Out of Scope for v1:** In-app notification list, unread-count indicator, push notifications, SMS notifications, and notification of any contact-sharing or match-flow event.

### 4.8 Admin Panel

**Description:** v1 uses the stock Django admin (`django.contrib.admin`) as the admin surface. Pending passport submissions appear in the admin queue, ordered FIFO. An admin opens a submission, reviews the NID front, NID back, selfie, and lifestyle fields, then chooses Approve or Reject with an optional reason code. There is no reports queue, no suspend/ban surface, and no custom admin views or dashboards in v1.

**Functional Requirements:**

#### FR-20: Admin authentication

Admin access uses Django admin's built-in authentication. Admin accounts are separate from tenant accounts and are not self-signup; they are created by an existing admin or via Django management command.

**Consequences (testable):**
- Admin login is the Django admin URL, separate from the tenant web app
- Admin actions are attributable to a specific admin account (Django admin's built-in `LogEntry` audit)
- Verification approve/reject actions run through VerificationService, the single source of truth for passport state transitions

**Out of Scope for v1:** Reports queue, suspend/ban admin actions, role-based admin permissions, admin activity analytics, custom admin views or dashboards.

**Cross-cutting note:** Admin functionality is described across FR-7, FR-8, FR-20. The admin panel is the stock Django admin, configured to surface the Verification queue.

## 5. Non-Goals (Explicit)

- **Not a landlord / mess-owner / subletter-facing product.** v1 serves tenants only. `[NON-GOAL for MVP]` Landlord-facing product is v2.
- **Not a property marketplace.** No full apartment listings, no photos of units, no virtual tours. v1 is the matching layer only.
- **Not a payment or rent-collection platform.** No rent, deposit, or fee processing in v1.
- **Not closing the police-verification loop.** Basha Pass gives tenants a verified credential; the thana submission remains the landlord's responsibility. `[NON-GOAL for MVP]` Future partnership with police or integration with national eKYC may close this loop in v2+.
- **Not a chat platform.** v1 deliberately hands off to email/phone/WhatsApp after the first reply. Building a chat product would be a different company.
- **Not a city beyond Dhaka at launch.** v1 is single-city. `[NON-GOAL for MVP]` Second-city expansion is v2, gated by verified-tenant density.
- **Not a monetized product.** Free at launch. `[NON-GOAL for MVP]` Monetization (employer partnerships, mess-owner subscription, featured listings, financial product partnerships) deferred to a later phase.
- **Not a government eKYC integration.** v1 uses manual review. `[NON-GOAL for MVP]` Integration with government NID API or partner KYC (bKash/Nagad/SSL) is v2.
- **Not an algorithmic matching product.** v1 uses 6 explicit filters; no ML matching. The simplicity is the product.
- **Not an enterprise / B2B platform.** No corporate housing, no bulk tenant onboarding, no property manager dashboard.
- **Not a regulated financial product.** No money flows through the platform, so PCI / financial regulatory frameworks do not apply in v1.
- **Not a content moderation heavy-lift.** v1 has no in-app report flow and no admin moderation queue. Off-platform escalations are handled manually by the founding team through support channels. No NLP moderation in v1.

## 6. MVP Scope

### 6.1 In Scope

- Responsive web app (mobile-first, works on Android Chrome, iOS Safari, desktop browsers)
- Email + password signup with 6-digit email-verification token (5-min expiry, ≤3 resends)
- Tenant Passport: NID front + back + selfie + 6 lifestyle fields, immutable after verification
- Verified-badge display on Listings and passport header
- Listing creation by verified tenants (kind=seat/room, area, rent, rent_unit, photos 1–7, 4 preference fields, optional body)
- Listing feed with filters (area, budget slider, kind, rent_unit, gender, occupation, smoking, sleep)
- Listing detail with contact-info visibility gated on viewer verification state (soft-gate)
- "Your listings" surface for the lister's own active and archived listings, with Edit (rent/body/photos) and Withdraw
- 3-active-listing cap and 60-day auto-archive
- Stock Django admin for verification review (NID front/back/selfie, approve/reject with reason codes); no custom admin UI
- Email notifications for verification status changes (5-min SLA, RESOLVED 2026-08-30)
- Audit trail for verification decisions
- English-only UI in v1 (Bangla support deferred to v2)
- Single-city launch: Dhaka only
- Money: integer BDT/taka only; no paisa, no decimals, no fractional values

### 6.2 Out of Scope for MVP

- **In-app chat / message thread / both-tap contact-share / contact visibility to unverified viewers / match closure / post-match survey / in-app notification list** — all flow surfaces are deferred to v2; v1 hands off to email/phone/WhatsApp at the moment of contact exchange.
- **In-app report flow and admin suspend/ban actions** — both deferred to v2; trust in v1 is anchored in NID verification.
- **Landlord / mess-owner / subletter product** — v2. Deferred because the wedge in v1 is tenant-side discovery.
- **Real government NID eKYC API** — v2. v1 manual review is acceptable for the launch scale.
- **Multi-city launch beyond Dhaka** — v2. Architecture supports it; launch is single-city.
- **Property listings for full apartments** (whole flats) — v2. v1 is seat/room inventory only.
- **Maps, virtual tours, address-level geocoding** — v2. v1 uses named sub-area selectors from a fixed list.
- **Payment / rent / deposit handling** — Deferred indefinitely. Not core to the matching wedge.
- **Police-verification submission to local thana** — v2+. Requires partnership with law enforcement; outside v1 scope.
- **Monetization of any kind** — Free at launch. Business model deferred.
- **Push notifications, SMS notifications** — v2. Email only.
- **Algorithmic / ML matching** — v2+. Explicit filters only in v1.
- **Tenant-to-tenant blocking** — v2. v1 has no in-app report flow.
- **Profile editing post-verification** — v2. Reduces fraud surface in v1.
- **Browser push, native mobile apps** — v2. Responsive web only in v1.
- **Multi-language support (Bangla or others)** — v2. English-only in v1.
- **Account deletion (FR-2)** — Out of scope per corrected scope. Re-introduce before public launch.

## 7. Success Metrics

**Primary**

- **SM-1: Verified passport creation rate** — Number of Tenant Passports created and approved within 90 days of launch. Target: ≥ 500. Validates FR-3, FR-7, FR-8.

- **SM-2: Successful matches reported** — Number of post-match surveys indicating a tenant "connected" with another tenant (Yes). Target: ≥ 100 within 90 days. Validates FR-13, FR-15.

- **SM-3: Verification quality** — Percentage of verified passports later disputed or revoked for fraud or quality reasons. Target: ≤ 5%. Validates FR-7, FR-8, FR-9.

**Secondary**

- **SM-4: Median time to first match** — Median time from a tenant's first "Looking For" post to their first reply. Target: ≤ 7 days. Validates FR-10, FR-11, FR-13.

- **SM-5: Match satisfaction** — Post-move survey (post-30-days): "Would you use Basha Pass again?" Target: ≥ 70% Yes. Validates FR-15, UJ-3.

- **SM-6: 30-day retention** — Percentage of verified tenants who return to the app within 30 days of passport verification. Target: ≥ 40%. Validates FR-1 (session persistence), FR-11 (feed engagement).

- **SM-7: Verification queue latency** — Median time from passport submission to verification decision. Target: ≤ 24 hours. Validates FR-7, FR-9.

**Counter-metrics (do not optimize)**

- **SM-C1: Number of reports filed per 100 active tenants.** Should *not* be driven to zero (low reports could mean tenants aren't reporting real issues, OR it could mean the platform is safe — both are good; high reports could mean either real problems OR a few bad actors being widely flagged, which is also informative). Counterbalances SM-3 and SM-5. The brief's success requires that reports are being filed, reviewed, and acted on — not that they disappear.

- **SM-C2: Verification approval rate.** Should *not* approach 100% (would suggest rubber-stamping). Should *not* drop below ~70% (would suggest overly strict review). Target band: 75–90%. Counterbalances SM-3.

- **SM-C3: Time spent in admin dashboard per verification.** Should *not* approach zero (would suggest inadequate review). Target band: 30 seconds – 3 minutes per submission. Counterbalances SM-7.

## 8. Open Questions

1. ~~**Email provider.**~~ **(RESOLVED 2026-08-30: Django SMTP integrated with Gmail SMTP for v1. 500 emails/day cap confirmed as v1 design ceiling. UX: 6-digit verification token, 5-min expiry, single-use, max 3 resends per signup.)** Operational follow-up: monitor actual send volume vs. 500/day cap; switch to Google Workspace SMTP (~2,000/day) if approached [Owner: Architect, revisit at 250 verified tenants with active signup volume].
2. **NID photo storage.** Where are NID photos stored, with what retention policy, with what encryption-at-rest posture, and what is the deletion-on-account-deletion guarantee? [Owner: Architect. Revisit at architecture phase.]
3. **Privacy policy.** What is the public-facing privacy policy text, specifically around NID photo retention, audit-trail retention, and post-deletion data purge? [Owner: PM. Revisit before public launch.]
4. ~~**Bangla/English UI ratio.**~~ **(RESOLVED 2026-08-30: English-only UI in v1. Bangla support deferred to v2.)**
5. ~~**Crisis hotline content.**~~ **(RESOLVED 2026-08-30: Bangladesh National Emergency Service — 999 — is the v1 default. Additional hotlines may be added based on user-research findings.)** Remaining question: whether to add secondary context-specific hotlines (women's safety, labor-rights, etc.) and in which scenarios each applies [Owner: PM. Revisit before public launch].
6. **Admin scale.** What is the maximum sustainable verification queue size for a single admin, and when does the team need to add a second reviewer or a temporary reviewer process? [Owner: PM. Revisit at SM-7 review (day 30).]
7. **Display name policy.** Should display names be moderated (no slurs, no contact info embedded, no impersonation), and if so, manually or with a blocklist? [Owner: PM. Revisit at UX phase.]
8. **Email cost budget.** Google SMTP via Workspace is approximately free at v1 scale (within daily caps); cost only emerges if v1 exceeds ~2,000 emails/day. Revisit at 1,000 verified tenants. [Owner: Architect.]
9. **Government eKYC timeline.** When and with which partner should v2 eKYC integration begin? [Owner: PM. Revisit at v2 planning.]
10. **Second-city criteria.** What metric (verified-tenant count, specific partner, specific demand signal) triggers second-city expansion? [Owner: PM. Revisit at v2 planning.]
11. **Bangladesh user email reality.** Many target users (students, garments workers) may not have reliable personal email accounts. Should Basha Pass require email verification before allowing passport creation, or allow deferred verification with limited functionality? `[NOTE FOR PM: this is a v1 success-risk question — if the persona lacks email access, the funnel breaks.]` [Owner: PM. Revisit before launch; validate via user research.]

## 9. Assumptions Index

Inline `[ASSUMPTION]` tags surfaced for review. All items below are **RESOLVED** as of 2026-08-30 — full resolution text is preserved in `.memlog.md`.

| ID | Topic | Resolved value |
|---|---|---|
| §2.1 | UI language | English-only in v1; Bangla deferred to v2 |
| §2.3 UJ-5 | Crisis hotline | 999 (Bangladesh National Emergency Service) as v1 default |
| §4.1 FR-1 | Email provider | Django SMTP + Gmail SMTP, 500 emails/day ceiling |
| §4.1 FR-1 | Verification token UX | 6-digit, 5-min expiry, single-use, max 3 resends/signup |
| §4.1 FR-1 | Password complexity | ≥8 chars + uppercase + lowercase + number + special char (all four required) |
| §4.1 FR-2 | Account deletion grace | 30 days, hard-delete after |
| §4.2 FR-3 | Passport edit-after-verify | Immutable after verification in v1; edit is v2 |
| §4.2 FR-4 | Lifestyle fields | 6 fields: gender, occupation, smoking, sleep, area, budget |
| §4.2 FR-4 | Budget slider range | Dynamic from active Looking-For posts in area; seeded ৳500–৳50,000 |
| §4.2 FR-4 | Area options | 13 canonical Dhaka sub-areas locked for v1 |
| §4.2 FR-6 | Display name length | 3–32 characters |
| §4.3 FR-9 | Re-submission cooldown | 24 hours, server-enforced |
| §4.5 FR-13 | Post-author notifications | In-app primary; email for first reply, contact-share, report outcome |
| §4.7 FR-18 | Verification SLA | Email sent within 5 minutes of status change |

**Open `[ASSUMPTION]` tags still inline in the PRD** (not yet promoted to resolutions — see `.memlog.md` for tracking): seed-value floors for the dynamic budget slider (৳500 / ৳50,000 until natural distribution emerges), Gmail SMTP send-volume monitoring trigger (~400 emails/day → migrate to Workspace SMTP), and architecture-phase items (NID photo storage encryption-at-rest, audit-trail retention period, key management).

---

**End of PRD v1 draft.**
