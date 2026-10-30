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
