# Supabase API Keys Integration Design

**Date:** 2026-03-04
**Branch:** feat/clerk-auth
**Status:** Approved

## Context

The `api-keys-page.tsx` component currently stores API keys in localStorage with mock data and client-side key generation using `Math.random()`. This design replaces that with a real Supabase backend.

API keys in Servo authenticate requests to Servo's own inference endpoint — the key IS the user identity for API calls (like OpenAI keys).

## Security: Bot/Spam Concern

Bots spamming the dashboard CRUD endpoints is not a concern — those are behind Clerk auth. The concern becomes real when the inference endpoint goes live. Mitigations:

- **Key entropy:** 128-bit random keys (`crypto.randomBytes(16).toString('hex')`) make brute-force computationally infeasible (2^128 guesses needed)
- **Rate limiting:** Apply IP-based rate limiting to the inference endpoint (future work)
- **Real threat is key leaks** — not guessing. Key hygiene (never log, never commit) matters more than brute-force protection.

## Architecture: Option A — Service Role Key in API Routes

Clerk handles authentication. API routes use the Supabase service role key server-side. The Clerk `userId` is stored as a foreign key in Supabase.

```
Browser → Clerk session → Next.js API route → Supabase (service role)
```

The anon/publishable key is not used for CRUD operations.

## Data Model

```sql
create table api_keys (
  id          uuid primary key default gen_random_uuid(),
  user_id     text not null,
  name        text not null,
  key         text not null unique,
  key_prefix  text not null,
  key_suffix  text not null,
  model       text not null,
  tags        text[] not null default '{}',
  requests    integer not null default 0,
  cost        numeric(10,4) not null default 0,
  status      text not null default 'active' check (status in ('active', 'inactive')),
  created_at  timestamptz not null default now(),
  last_used   timestamptz
);

create index on api_keys (user_id);
create index on api_keys (key);
```

Key format: `sk_live_<32 hex chars>` — generated server-side only. Full key returned once at creation, never again.

## API Routes

```
app/api/keys/
  route.ts          GET  → list user's keys (masked, no full key)
                    POST → create new key (returns full key once)
  [id]/
    route.ts        DELETE → revoke key
    rotate/
      route.ts      POST → new key value, same metadata (returns full key once)
```

All routes: `auth()` from Clerk → 401 if unauthenticated → Supabase query filtered by `user_id`.

## Component Changes

`api-keys-page.tsx`:
- Remove localStorage state initializer and sync effect
- Add `useEffect` to fetch `GET /api/keys` on mount (with loading/error state)
- `handleAddKey` → `POST /api/keys` → one-time key reveal dialog → refresh list
- `handleRevoke` → `DELETE /api/keys/[id]` → remove from state
- Rotate → `POST /api/keys/[id]/rotate` → one-time key reveal dialog
- Full key value never stored in list state after reveal dialog closes

## Environment Variables

```bash
# .env.local (never commit)
NEXT_PUBLIC_SUPABASE_URL=https://gsxwswuowngwjrnzmxzy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_hmKyaNj7GgNvZHyK8kt9kg_s66cZOxz
SUPABASE_SERVICE_ROLE_KEY=<service_role key from Supabase dashboard>
```

## Dependencies

```bash
npm install @supabase/supabase-js
```

## Deliverables

1. `supabase/migrations/001_api_keys.sql` — table + indexes
2. `lib/supabase.ts` — server-side Supabase client
3. `app/api/keys/route.ts` — GET + POST
4. `app/api/keys/[id]/route.ts` — DELETE
5. `app/api/keys/[id]/rotate/route.ts` — POST rotate
6. `components/api-keys-page.tsx` — refactored to use API routes
