# Servo — CLAUDE.md

## Project Overview

Servo is an LLM routing and cost optimization platform. It classifies user prompts by complexity and routes them to the cheapest appropriate model tier, targeting up to 80% inference cost savings. Built as a CS206 (SPM) university project.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 16 (App Router), React 19 |
| Language | TypeScript 5 (strict mode) |
| Styling | Tailwind CSS 4 + shadcn/ui (Radix UI) |
| Auth | Clerk (`middleware.ts`) |
| Database | Supabase (PostgreSQL) |
| Graph UI | @xyflow/react (routing diagram) |
| Charts | Recharts |
| SDKs | JS/TS SDK (`SDK/NPM SDK/`), Python SDK (`SDK/Python SDK/`) |
| Validation | Zod + React Hook Form |

## Key Directories

| Path | Purpose |
|------|---------|
| `app/` | Next.js App Router — pages and API routes |
| `app/api/` | REST endpoints (keys, routing, SDK) |
| `components/` | Feature and UI components |
| `components/ui/` | shadcn/ui primitives |
| `components/nodes/` | ReactFlow custom node components |
| `lib/` | Supabase client, shared utilities |
| `SDK/NPM SDK/src/` | JS/TS SDK implementation |
| `SDK/Python SDK/servo_sdk/` | Python SDK implementation |
| `supabase/migrations/` | Versioned SQL migrations |
| `docs/plans/` | Design docs and development plans |

## Essential Commands

### Web App
```bash
npm run dev      # Dev server → http://localhost:3000
npm run build    # Production build
npm run lint     # ESLint
```

### Python SDK
```bash
pip install -e ".[dev]"   # Install with dev deps
pytest                    # Run tests
```

### JS SDK
```bash
npm run build   # Compile TypeScript → dist/
```

## Environment Variables

Copy `.env.example` to `.env.local`. Key variables:
- `NEXT_PUBLIC_CLERK_*` — Clerk auth keys
- `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Supabase client
- `SUPABASE_SERVICE_ROLE_KEY` — Supabase admin (API routes only)
- `GOOGLE_AI_STUDIO_API_KEY` — LLM provider key
- `CLASSIFIER_ENDPOINT` / `CLASSIFIER_MODEL` — Local Llama.cpp classifier server

## API Routes

| Route | Methods | Purpose |
|-------|---------|---------|
| `app/api/keys/route.ts` | GET, POST | List and create API keys |
| `app/api/keys/[id]/route.ts` | GET, DELETE | Single key operations |
| `app/api/keys/[id]/rotate/route.ts` | POST | Rotate a key |
| `app/api/routing/route.ts` | GET, PUT | Routing config CRUD |
| `app/api/sdk/validate/route.ts` | POST | Validate SDK API key |
| `app/api/sdk/routing-config/route.ts` | GET | Fetch routing config for SDK |

All `/api/keys` and `/api/routing` routes require Clerk auth (`userId` from `auth()`). `/api/sdk/*` routes use Bearer token auth against the `api_keys` table.

## Database Tables (Supabase)

- `api_keys` — user API keys with `name`, `key`, `key_prefix`, `key_suffix`, `model`, `tags`, `status`, `last_used`
- `routing_configs` — per-user routing config stored as JSON `{ default_category_id, categories[] }`

## Additional Documentation

Check these files when working on related areas:

- `.claude/docs/architectural_patterns.md` — data flow, auth patterns, SDK design, ReactFlow graph pattern, component hierarchy
