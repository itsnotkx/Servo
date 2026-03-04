# Clerk Auth + Marketing Landing Page — Design

**Date:** 2026-03-04
**Status:** Approved

## Overview

Add Clerk authentication to Servo. The current single-page dashboard becomes a protected `/dashboard` route. A public marketing landing page replaces `/`. A documentation placeholder is added at `/documentation`. Clerk middleware gates all dashboard routes.

## Route Structure

```
app/
├── layout.tsx                     ← Add ClerkProvider (root)
├── middleware.ts                  ← NEW: route protection via clerkMiddleware
│
├── page.tsx                       ← REPLACE: public marketing landing page
├── documentation/
│   └── page.tsx                   ← NEW: public documentation placeholder
├── sign-in/[[...sign-in]]/
│   └── page.tsx                   ← NEW: Clerk SignIn component (centered layout)
├── sign-up/[[...sign-up]]/
│   └── page.tsx                   ← NEW: Clerk SignUp component (centered layout)
│
└── dashboard/
    └── page.tsx                   ← MOVE: current app/page.tsx contents
```

## Middleware

- Uses `clerkMiddleware()` with `createRouteMatcher`
- Public routes: `/`, `/documentation`, `/sign-in/(.*)`, `/sign-up/(.*)`
- All other routes require auth
- Unauthenticated access to `/dashboard` redirects to `/sign-in`

## Landing Page (`/`)

Sections (top to bottom):

1. **Navbar** — Logo, nav links (Features, How It Works, Documentation), Sign In + Get Started buttons. Sticky.
2. **Hero** — Headline, subheading on cost/performance routing, two CTAs: "Get Started Free" (→ `/sign-up`) and "View Docs" (→ `/documentation`)
3. **Features** — 3-column card grid: Intelligent Routing, Cost Optimization, Provider Flexibility
4. **How It Works** — 3-step numbered flow: Send request → Classify complexity → Right model responds
5. **CTA Banner** — "Start routing smarter" + Sign Up button
6. **Footer** — Logo, Documentation link, Sign In link

Built with existing shadcn/ui + Tailwind. No new UI dependencies.

## Sign In / Sign Up Pages

- Centered layout wrapping Clerk's `<SignIn />` and `<SignUp />` components
- Clerk handles all UI (email/password, OAuth, error states, email verification)
- After sign-in: redirect to `/dashboard`

## Documentation Page (`/documentation`)

- Public (not gated)
- Simple centered page: "Documentation" heading + "Coming soon" subtext + link back to dashboard

## Sidebar Changes

- Replace hardcoded `"your@startup.com"` with `useUser().user?.emailAddresses[0].emailAddress`
- Wire "Sign Out" button to `useClerk().signOut()` with redirect to `/`

## Dependencies

- `@clerk/nextjs` (new)
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` env vars required
- `NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in`
- `NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up`
- `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard`
- `NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard`
