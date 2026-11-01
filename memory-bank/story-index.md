# Story Index

## 001-project-init-and-landing

### 001-core-foundation
- [x] [`001-django-project-scaffolding`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/001-project-init-and-landing/units/001-core-foundation/stories/001-django-project-scaffolding.md) - Setup Poetry, Django 5.2, split settings, and test harness (Must, assigned: `001-core-foundation`)
- [x] [`002-base-layout-and-design-tokens`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/001-project-init-and-landing/units/001-core-foundation/stories/002-base-layout-and-design-tokens.md) - Base HTML template with brand tokens and responsive layout structure (Must, assigned: `001-core-foundation`)

### 002-landing-page-ui
- [x] [`003-landing-hero-and-passport-showcase`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/001-project-init-and-landing/units/002-landing-page-ui/stories/003-landing-hero-and-passport-showcase.md) - Hero section, search filter teaser, and Tenant Passport showcase card (Must, assigned: `002-landing-page-ui`)
- [x] [`004-how-it-works-and-navigation`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/001-project-init-and-landing/units/002-landing-page-ui/stories/004-how-it-works-and-navigation.md) - Navigation navbar, "How It Works" steps, trust panel, and footer (Must, assigned: `002-landing-page-ui`)

## 002-user-authentication-and-registration

### 001-account-identity-service
- [x] [`005-custom-user-model`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/002-user-authentication-and-registration/units/001-account-identity-service/stories/005-custom-user-model.md) - Custom User model with UUID4 PK, case-insensitive email, and UserManager (Must, assigned: `003-account-identity-service`)
- [x] [`006-email-verification-token-and-service`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/002-user-authentication-and-registration/units/001-account-identity-service/stories/006-email-verification-token-and-service.md) - EmailVerificationToken model (hashed OTP, 5m expiry), AccountService, and email dispatch (Must, assigned: `003-account-identity-service`)
- [x] [`007-password-validation-and-auth-backend`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/002-user-authentication-and-registration/units/001-account-identity-service/stories/007-password-validation-and-auth-backend.md) - 5-rule password complexity validator, case-insensitive auth backend, 30-day session config (Must, assigned: `003-account-identity-service`)

### 002-auth-ui-views
- [x] [`008-signup-and-verify-email-views`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/002-user-authentication-and-registration/units/002-auth-ui-views/stories/008-signup-and-verify-email-views.md) - Signup view, verify email OTP interface, HTMX resend trigger, and welcome view (Must, assigned: `004-user-auth-ui`)
- [x] [`009-login-logout-and-session-views`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/002-user-authentication-and-registration/units/002-auth-ui-views/stories/009-login-logout-and-session-views.md) - Login view with 30-day session persistence, logout endpoint, and unverified guards (Must, assigned: `004-user-auth-ui`)
- [x] [`010-password-reset-views`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/002-user-authentication-and-registration/units/002-auth-ui-views/stories/010-password-reset-views.md) - Password reset request and confirmation views with token generation and reset email (Should, assigned: `004-user-auth-ui`)

## 003-tenant-passport-and-verification

### 001-passport-and-verification-domain
- [x] [`011-passport-and-lifestyle-models`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/003-tenant-passport-and-verification/units/001-passport-and-verification-domain/stories/011-passport-and-lifestyle-models.md) - Passport & LifestyleProfile models, 6 dimensions, post-verify immutability (Must, assigned: `005-passport-verification-service`)
- [x] [`012-verification-model-and-private-storage`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/003-tenant-passport-and-verification/units/001-passport-and-verification-domain/stories/012-verification-model-and-private-storage.md) - Verification model, private PII storage under media_private/, 5-member canonical reject reasons enum (Must, assigned: `005-passport-verification-service`)
- [x] [`013-verification-service-cooldown-and-audit`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/003-tenant-passport-and-verification/units/001-passport-and-verification-domain/stories/013-verification-service-cooldown-and-audit.md) - VerificationService sole mutator, 24h cooldown, AuditService append-only log, direct email dispatch (Must, assigned: `005-passport-verification-service`)
- [x] [`014-admin-verification-queue`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/003-tenant-passport-and-verification/units/001-passport-and-verification-domain/stories/014-admin-verification-queue.md) - Django Admin FIFO verification review queue with high-res document previews, approve/reject/escalate actions (Must, assigned: `005-passport-verification-service`)

### 002-passport-verification-ui
- [x] [`015-passport-submission-wizard`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/003-tenant-passport-and-verification/units/002-passport-verification-ui/stories/015-passport-submission-wizard.md) - Multi-step wizard capturing display name, 6 lifestyle dimensions, and NID/selfie uploads (Must, assigned: `006-passport-verification-ui`)
- [x] [`016-verification-status-dashboards`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/003-tenant-passport-and-verification/units/002-passport-verification-ui/stories/016-verification-status-dashboards.md) - Unverified teaser, in-review status, rejection screen with 24h countdown timer, and verified passport badge (Must, assigned: `006-passport-verification-ui`)

## 004-create-and-manage-listing

### 001-listing-domain-service
- [x] [`017-listing-and-photo-models`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/004-create-and-manage-listing/units/001-listing-domain-service/stories/017-listing-and-photo-models.md) - Listing & ListingPhoto models, UUIDv7 PK, cross-field constraints, area array (Must, assigned: `007-listing-domain-service`)
- [x] [`018-listing-service-and-active-cap`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/004-create-and-manage-listing/units/001-listing-domain-service/stories/018-listing-service-and-active-cap.md) - ListingService sole mutator, 3-active cap, edit locked fields, withdraw, auto-archive (Must, assigned: `007-listing-domain-service`)
- [x] [`019-listing-photo-storage-service`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/004-create-and-manage-listing/units/001-listing-domain-service/stories/019-listing-photo-storage-service.md) - Listing photo storage service, Pillow validation, 1-7 photo limits, public media path (Must, assigned: `007-listing-domain-service`)

### 002-listing-authoring-and-management-ui
- [x] [`020-verified-tenant-listing-gate`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/004-create-and-manage-listing/units/002-listing-authoring-and-management-ui/stories/020-verified-tenant-listing-gate.md) - VerifiedTenantRequiredMixin gating authoring CBVs with instructional redirects (Must, assigned: `008-listing-management-ui`)
- [x] [`021-listing-create-form-and-view`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/004-create-and-manage-listing/units/002-listing-authoring-and-management-ui/stories/021-listing-create-form-and-view.md) - Multi-section listing creation view, form cross-validation, photo uploader & advisory note (Must, assigned: `008-listing-management-ui`)
- [x] [`022-lister-management-dashboard`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/004-create-and-manage-listing/units/002-listing-authoring-and-management-ui/stories/022-lister-management-dashboard.md) - "Your Listings" dashboard view with status badges, active/archived toggle tabs, quick actions (Must, assigned: `008-listing-management-ui`)
- [x] [`023-listing-edit-and-withdraw-views`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/004-create-and-manage-listing/units/002-listing-authoring-and-management-ui/stories/023-listing-edit-and-withdraw-views.md) - Edit view for mutable terms, locked-field protection, and manual withdrawal modal action (Must, assigned: `008-listing-management-ui`)

## 005-public-listing-feed-and-search

### 001-listing-feed-query-and-consent
- [x] [`024-listing-consent-service-and-projection`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/005-public-listing-feed-and-search/units/001-listing-feed-query-and-consent/stories/024-listing-consent-service-and-projection.md) - ConsentService & viewer-scoped PII projection shielding contact info (Must, assigned: `009-listing-feed-query-and-consent`)
- [x] [`025-listing-feed-query-and-compatibility`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/005-public-listing-feed-and-search/units/001-listing-feed-query-and-consent/stories/025-listing-feed-query-and-compatibility.md) - ListingFeedQuery read model, multi-axis filtering, sorting, and 6-axis compatibility score (Must, assigned: `009-listing-feed-query-and-consent`)

### 002-listing-feed-and-detail-ui
- [x] [`026-feed-view-and-filter-ui`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/005-public-listing-feed-and-search/units/002-listing-feed-and-detail-ui/stories/026-feed-view-and-filter-ui.md) - Public listing feed view, offcanvas filter drawer, & sorting controls matching Mockup 03 (Must, assigned: `010-listing-discovery-and-detail-ui`)
- [x] [`027-listing-card-and-compatibility-ui`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/005-public-listing-feed-and-search/units/002-listing-feed-and-detail-ui/stories/027-listing-card-and-compatibility-ui.md) - Reusable listing card with 0–6 compatibility match dots indicator (Must, assigned: `010-listing-discovery-and-detail-ui`)
- [x] [`028-listing-detail-and-gated-contact-ui`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/005-public-listing-feed-and-search/units/002-listing-feed-and-detail-ui/stories/028-listing-detail-and-gated-contact-ui.md) - Listing detail page, photo gallery carousel, soft-gated contact card, and audit logging (Must, assigned: `010-listing-discovery-and-detail-ui`)


## 006-account-settings-and-preferences

### 001-account-preference-domain
- [ ] [`029-lifestyle-preference-mutability-and-profile-domain`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/006-account-settings-and-preferences/units/001-account-preference-domain/stories/029-lifestyle-preference-mutability-and-profile-domain.md) - LifestyleProfile mutability decoupling for search area/budget and profile domain mutations (Must, assigned: `011-account-preference-domain`)
- [ ] [`030-password-change-and-security-audit-service`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/006-account-settings-and-preferences/units/001-account-preference-domain/stories/030-password-change-and-security-audit-service.md) - In-app password rotation with complexity validation and append-only audit tracking (Must, assigned: `011-account-preference-domain`)

### 002-account-settings-ui
- [ ] [`031-account-settings-hub-and-profile-form-ui`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/006-account-settings-and-preferences/units/002-account-settings-ui/stories/031-account-settings-hub-and-profile-form-ui.md) - Gated Account Settings hub view, profile card with display name & phone form, navbar link (Must, assigned: `012-account-settings-ui`)
- [ ] [`032-location-preference-and-password-change-ui`](file:///home/bs01496/Documents/LMS/basa-pass/memory-bank/intents/006-account-settings-and-preferences/units/002-account-settings-ui/stories/032-location-preference-and-password-change-ui.md) - Dhaka sub-area chip selector, budget inputs, and secure password change form (Must, assigned: `012-account-settings-ui`)
