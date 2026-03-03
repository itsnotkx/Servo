# Clerk Auth + Marketing Landing Page — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Clerk authentication, protect the dashboard behind auth, create a public marketing landing page at `/`, a sign-in/sign-up page pair, and a documentation placeholder.

**Architecture:** Clerk middleware protects all routes except `/`, `/documentation`, `/sign-in`, and `/sign-up`. The existing dashboard moves to `/dashboard`. A new marketing landing page replaces `/`. Clerk's hosted `<SignIn />` and `<SignUp />` components handle auth UI. The sidebar's hardcoded email and Sign Out button are wired to Clerk hooks.

**Tech Stack:** Next.js 16 (App Router), `@clerk/nextjs`, shadcn/ui, Tailwind CSS v4

---

## Pre-requisites

Before starting, you need a Clerk account and app:
1. Go to https://clerk.com and create a free account
2. Create a new application, choose "Email + Password" (and any OAuth you want)
3. From the Clerk dashboard → API Keys, copy:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - `CLERK_SECRET_KEY`

---

### Task 1: Install Clerk and configure environment

**Files:**
- Create: `.env.local`
- Modify: `package.json` (via npm install)

**Step 1: Install the Clerk Next.js SDK**

```bash
npm install @clerk/nextjs
```

Expected: `@clerk/nextjs` appears in `package.json` dependencies.

**Step 2: Create `.env.local` with Clerk keys**

Create `.env.local` in the project root:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
CLERK_SECRET_KEY=sk_test_YOUR_KEY_HERE

NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
```

Replace the placeholder values with your actual keys from the Clerk dashboard.

**Step 3: Verify .env.local is gitignored**

```bash
grep ".env.local" .gitignore
```

Expected: `.env.local` is listed. If not, add it.

**Step 4: Commit**

```bash
git add package.json package-lock.json
git commit -m "feat: install @clerk/nextjs"
```

---

### Task 2: Add ClerkProvider to root layout

**Files:**
- Modify: `app/layout.tsx`

**Step 1: Update `app/layout.tsx`**

Replace the entire file content with:

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Servo",
  description: "API Router Project for CS206G4T6",
  icons: {
    icon: "/servoLogo.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
```

**Step 2: Verify the dev server starts without errors**

```bash
npm run dev
```

Expected: Server starts on `http://localhost:3000` with no TypeScript or import errors.

**Step 3: Commit**

```bash
git add app/layout.tsx
git commit -m "feat: wrap app in ClerkProvider"
```

---

### Task 3: Create middleware for route protection

**Files:**
- Create: `middleware.ts` (project root, next to `package.json`)

**Step 1: Create `middleware.ts`**

```ts
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/documentation(.*)",
  "/sign-in(.*)",
  "/sign-up(.*)",
]);

export default clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
```

**Step 2: Verify unauthenticated redirect**

Run `npm run dev`, open `http://localhost:3000/dashboard` in a browser while not signed in.

Expected: Redirected to `/sign-in`.

**Step 3: Commit**

```bash
git add middleware.ts
git commit -m "feat: add clerk middleware, protect /dashboard"
```

---

### Task 4: Move dashboard to `/dashboard`

**Files:**
- Create: `app/dashboard/page.tsx`
- Modify: `app/page.tsx` (will be replaced with landing page in Task 6)

**Step 1: Create `app/dashboard/page.tsx`**

Copy the current contents of `app/page.tsx` exactly:

```tsx
'use client'

import { useState } from 'react'
import Sidebar from '@/components/sidebar'
import DashboardContent from '@/components/dashboard-content'

export default function Dashboard() {
  const [activePage, setActivePage] = useState('dashboard')

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <DashboardContent page={activePage} />
    </div>
  )
}
```

**Step 2: Verify dashboard loads**

Navigate to `http://localhost:3000/dashboard` after signing in (or temporarily remove middleware to test).

Expected: Dashboard renders with sidebar and content identical to before.

**Step 3: Commit**

```bash
git add app/dashboard/page.tsx
git commit -m "feat: move dashboard to /dashboard route"
```

---

### Task 5: Create sign-in and sign-up pages

**Files:**
- Create: `app/sign-in/[[...sign-in]]/page.tsx`
- Create: `app/sign-up/[[...sign-up]]/page.tsx`

**Step 1: Create `app/sign-in/[[...sign-in]]/page.tsx`**

```tsx
import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <SignIn />
    </div>
  );
}
```

**Step 2: Create `app/sign-up/[[...sign-up]]/page.tsx`**

```tsx
import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <SignUp />
    </div>
  );
}
```

**Step 3: Verify sign-in page**

Navigate to `http://localhost:3000/sign-in`.

Expected: Clerk's sign-in form renders centered on the page.

**Step 4: Verify sign-up page**

Navigate to `http://localhost:3000/sign-up`.

Expected: Clerk's sign-up form renders centered on the page.

**Step 5: Verify post-auth redirect**

Sign in with a test account.

Expected: Redirected to `/dashboard` after successful sign-in.

**Step 6: Commit**

```bash
git add app/sign-in app/sign-up
git commit -m "feat: add clerk sign-in and sign-up pages"
```

---

### Task 6: Wire sidebar to Clerk (email + sign out)

**Files:**
- Modify: `components/sidebar.tsx`

**Step 1: Update `components/sidebar.tsx`**

Replace the entire file:

```tsx
'use client';

import { BarChart3, CreditCard, Key, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUser, useClerk } from '@clerk/nextjs'

interface SidebarProps {
  activePage: string
  setActivePage: (page: string) => void
}

export default function Sidebar({ activePage, setActivePage }: SidebarProps) {
  const { user } = useUser()
  const { signOut } = useClerk()

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]

  const email = user?.emailAddresses[0]?.emailAddress ?? ''

  return (
    <div className="w-64 border-r border-border bg-sidebar flex flex-col">
      {/* Logo Section */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
            <span className="text-accent-foreground font-bold text-sm">S</span>
          </div>
          <h1 className="text-xl font-bold text-sidebar-foreground">Servo</h1>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = activePage === item.id
            return (
              <Button
                key={item.id}
                variant={isActive ? 'default' : 'ghost'}
                className={`w-full justify-start gap-3 text-base ${
                  isActive
                    ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent'
                }`}
                onClick={() => setActivePage(item.id)}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Button>
            )
          })}
        </div>
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-sidebar-border">
        <div className="bg-sidebar-accent bg-opacity-20 rounded-lg p-3 mb-4">
          <p className="text-xs text-sidebar-accent-foreground font-semibold mb-1">ACCOUNT</p>
          <p className="text-sm text-sidebar-foreground truncate">{email}</p>
        </div>
        <Button
          variant="outline"
          className="w-full text-sidebar-foreground border-sidebar-border hover:bg-sidebar-accent bg-transparent"
          onClick={() => signOut({ redirectUrl: '/' })}
        >
          Sign Out
        </Button>
      </div>
    </div>
  )
}
```

**Step 2: Verify email shows correctly**

Sign in and navigate to `/dashboard`.

Expected: Sidebar shows your actual Clerk account email, not `"your@startup.com"`.

**Step 3: Verify sign out**

Click "Sign Out".

Expected: Redirected to `/` (landing page). Navigating to `/dashboard` now redirects to `/sign-in`.

**Step 4: Commit**

```bash
git add components/sidebar.tsx
git commit -m "feat: wire sidebar email and sign out to clerk"
```

---

### Task 7: Create documentation placeholder page

**Files:**
- Create: `app/documentation/page.tsx`

**Step 1: Create `app/documentation/page.tsx`**

```tsx
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function DocumentationPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background text-foreground px-4">
      <div className="text-center max-w-md">
        <div className="w-12 h-12 bg-accent rounded-xl flex items-center justify-center mx-auto mb-6">
          <span className="text-accent-foreground font-bold text-lg">S</span>
        </div>
        <h1 className="text-4xl font-bold mb-4">Documentation</h1>
        <p className="text-muted-foreground text-lg mb-8">
          Full API reference and integration guides are coming soon.
        </p>
        <div className="flex gap-4 justify-center">
          <Button asChild>
            <Link href="/dashboard">Go to Dashboard</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/">Back to Home</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Verify documentation page is publicly accessible**

Open `http://localhost:3000/documentation` while signed out.

Expected: Page renders — no redirect to sign-in.

**Step 3: Commit**

```bash
git add app/documentation
git commit -m "feat: add documentation placeholder page"
```

---

### Task 8: Create the marketing landing page

**Files:**
- Modify: `app/page.tsx` (replace entirely)

**Step 1: Replace `app/page.tsx` with the full marketing page**

```tsx
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ArrowRight, Zap, DollarSign, Layers } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">

      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-accent rounded-lg flex items-center justify-center">
              <span className="text-accent-foreground font-bold text-xs">S</span>
            </div>
            <span className="font-bold text-lg">Servo</span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-foreground transition-colors">How It Works</a>
            <Link href="/documentation" className="hover:text-foreground transition-colors">Documentation</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Button variant="ghost" asChild>
              <Link href="/sign-in">Sign In</Link>
            </Button>
            <Button asChild>
              <Link href="/sign-up">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-28 text-center">
        <div className="inline-flex items-center gap-2 bg-accent/10 text-accent border border-accent/20 rounded-full px-4 py-1.5 text-sm font-medium mb-8">
          <Zap className="w-3.5 h-3.5" />
          Intelligent LLM Routing
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-tight">
          Route every request to<br />
          <span className="text-accent">the right model</span>
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
          Servo automatically classifies your prompts and routes them to the optimal model — cutting inference costs without sacrificing quality.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" className="gap-2 text-base px-8" asChild>
            <Link href="/sign-up">
              Get Started Free
              <ArrowRight className="w-4 h-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" className="text-base px-8 bg-transparent" asChild>
            <Link href="/documentation">View Docs</Link>
          </Button>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Everything you need to optimize LLM costs</h2>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto">Stop overpaying for simple requests. Servo routes intelligently so you only use expensive models when you actually need them.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="bg-card border-border p-8">
            <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center mb-5">
              <Zap className="w-5 h-5 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Intelligent Routing</h3>
            <p className="text-muted-foreground leading-relaxed">
              Automatically classify request complexity and route each prompt to the most appropriate model tier in milliseconds.
            </p>
          </Card>
          <Card className="bg-card border-border p-8">
            <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center mb-5">
              <DollarSign className="w-5 h-5 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Cost Optimization</h3>
            <p className="text-muted-foreground leading-relaxed">
              Route simple requests to lightweight models and save up to 80% on inference costs — with full visibility into spend per key.
            </p>
          </Card>
          <Card className="bg-card border-border p-8">
            <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center mb-5">
              <Layers className="w-5 h-5 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Provider Flexibility</h3>
            <p className="text-muted-foreground leading-relaxed">
              Built on Google AI Studio today, with a provider-agnostic architecture ready to support any LLM provider you need tomorrow.
            </p>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="border-y border-border bg-card/30">
        <div className="max-w-6xl mx-auto px-6 py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">How it works</h2>
            <p className="text-muted-foreground text-lg">Three steps. Zero configuration required.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Send your request',
                description: 'Point your application at the Servo API endpoint. No changes to your existing prompts needed.',
              },
              {
                step: '02',
                title: 'Servo classifies complexity',
                description: 'Our classifier analyses your prompt and scores it against your configured routing rules in real time.',
              },
              {
                step: '03',
                title: 'The right model responds',
                description: 'Simple requests go to fast, cheap models. Complex ones go to powerful models. You pay only for what the task actually needs.',
              },
            ].map(({ step, title, description }) => (
              <div key={step} className="flex flex-col items-start">
                <span className="text-5xl font-bold text-accent/20 mb-4">{step}</span>
                <h3 className="text-xl font-semibold mb-3">{title}</h3>
                <p className="text-muted-foreground leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Banner */}
      <section className="max-w-6xl mx-auto px-6 py-24 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">Start routing smarter today</h2>
        <p className="text-muted-foreground text-lg mb-8 max-w-lg mx-auto">
          Create a free account, generate an API key, and cut your LLM costs in minutes.
        </p>
        <Button size="lg" className="gap-2 text-base px-8" asChild>
          <Link href="/sign-up">
            Create Free Account
            <ArrowRight className="w-4 h-4" />
          </Link>
        </Button>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-accent rounded-md flex items-center justify-center">
              <span className="text-accent-foreground font-bold text-xs">S</span>
            </div>
            <span className="font-semibold">Servo</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <Link href="/documentation" className="hover:text-foreground transition-colors">Documentation</Link>
            <Link href="/sign-in" className="hover:text-foreground transition-colors">Sign In</Link>
          </div>
        </div>
      </footer>

    </div>
  )
}
```

**Step 2: Verify landing page**

Open `http://localhost:3000` while signed out.

Expected:
- Sticky navbar with Sign In and Get Started buttons
- Hero with headline and two CTAs
- Features section with 3 cards
- How It Works section with 3 numbered steps
- CTA banner
- Footer

**Step 3: Verify navbar links work**

- Click "Sign In" → lands on `/sign-in`
- Click "Get Started" → lands on `/sign-up`
- Click "Documentation" → lands on `/documentation`
- Anchor links `#features` and `#how-it-works` scroll to correct sections

**Step 4: Commit**

```bash
git add app/page.tsx
git commit -m "feat: add marketing landing page"
```

---

### Task 9: Final wiring check and cleanup

**Files:**
- No new files — verification only

**Step 1: Full auth flow walkthrough**

1. Open `http://localhost:3000` — landing page visible, no auth required
2. Click "Get Started Free" → `/sign-up` — Clerk sign-up form visible
3. Create a test account
4. Expected: redirected to `/dashboard`
5. Confirm sidebar shows your real email
6. Click "Sign Out"
7. Expected: redirected to `/`
8. Click "Sign In" → `/sign-in` — sign in with test account
9. Expected: redirected to `/dashboard`
10. Manually navigate to `http://localhost:3000/documentation` — accessible without auth
11. Manually navigate to `http://localhost:3000` — accessible without auth

**Step 2: Commit (if any leftover changes)**

```bash
git add -A
git status  # confirm nothing unexpected is staged
git commit -m "feat: complete clerk auth integration"
```
