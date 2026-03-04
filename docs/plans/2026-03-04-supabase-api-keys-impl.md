# Supabase API Keys Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace localStorage-backed API key management with Supabase persistence, using Next.js API routes authenticated via Clerk.

**Architecture:** Clerk authenticates dashboard users. API routes extract `userId` from Clerk, then query Supabase using the service role key (server-only). The `api_keys` table is scoped per user. Full key value is returned exactly once on creation/rotation.

**Tech Stack:** Next.js 16 App Router, Clerk `@clerk/nextjs`, `@supabase/supabase-js`, TypeScript, Node.js `crypto` module (built-in).

---

### Task 1: Install Supabase client library

**Files:**
- Modify: `package.json` (via npm)

**Step 1: Install the package**

```bash
npm install @supabase/supabase-js
```

**Step 2: Verify install**

```bash
cat package.json | grep supabase
```

Expected: `"@supabase/supabase-js": "^2.x.x"`

**Step 3: Commit**

```bash
git add package.json package-lock.json
git commit -m "chore: add @supabase/supabase-js"
```

---

### Task 2: Create the database table

**Files:**
- Create: `supabase/migrations/001_api_keys.sql`

**Step 1: Create the migration file**

Create `supabase/migrations/001_api_keys.sql` with this exact content:

```sql
create table if not exists api_keys (
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

create index if not exists api_keys_user_id_idx on api_keys (user_id);
create index if not exists api_keys_key_idx on api_keys (key);
```

**Step 2: Run it in Supabase**

Go to: Supabase Dashboard → SQL Editor → New query → paste the file contents → Run.

Expected: "Success. No rows returned."

**Step 3: Verify the table exists**

In the Supabase SQL Editor run:
```sql
select column_name, data_type from information_schema.columns
where table_name = 'api_keys' order by ordinal_position;
```

Expected: 13 rows listing all columns.

**Step 4: Commit**

```bash
git add supabase/migrations/001_api_keys.sql
git commit -m "feat: add api_keys table migration"
```

---

### Task 3: Create the server-side Supabase client

**Files:**
- Create: `lib/supabase.ts`

**Step 1: Create the file**

Create `lib/supabase.ts`:

```ts
import { createClient } from '@supabase/supabase-js'

if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
  throw new Error('Missing NEXT_PUBLIC_SUPABASE_URL')
}
if (!process.env.SUPABASE_SERVICE_ROLE_KEY) {
  throw new Error('Missing SUPABASE_SERVICE_ROLE_KEY')
}

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
)
```

Note: this file must only ever be imported in server-side code (API routes, Server Components). Never import it in a `'use client'` file.

**Step 2: Verify TypeScript compiles**

```bash
npx tsc --noEmit
```

Expected: no errors.

**Step 3: Commit**

```bash
git add lib/supabase.ts
git commit -m "feat: add server-side Supabase client"
```

---

### Task 4: Create GET and POST /api/keys route

**Files:**
- Create: `app/api/keys/route.ts`

**Step 1: Create the route handler**

Create `app/api/keys/route.ts`:

```ts
import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import crypto from 'crypto'

export async function GET() {
  const { userId } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { data, error } = await supabase
    .from('api_keys')
    .select('id, name, key_prefix, key_suffix, model, tags, requests, cost, status, created_at, last_used')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json(data)
}

export async function POST(request: Request) {
  const { userId } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const body = await request.json()
  const { name, model, tags } = body

  if (!name || !model) {
    return NextResponse.json({ error: 'name and model are required' }, { status: 400 })
  }

  const raw = crypto.randomBytes(16).toString('hex') // 128-bit entropy
  const key = `sk_live_${raw}`

  const { data, error } = await supabase
    .from('api_keys')
    .insert({
      user_id: userId,
      name,
      key,
      key_prefix: 'sk_live_',
      key_suffix: raw.slice(-4),
      model,
      tags: Array.isArray(tags) ? tags : [],
    })
    .select('id, name, key_prefix, key_suffix, model, tags, requests, cost, status, created_at, last_used')
    .single()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  // Full key returned once only — never returned again after this
  return NextResponse.json({ ...data, key }, { status: 201 })
}
```

**Step 2: Start dev server and test GET (must be logged in via browser first)**

```bash
npm run dev
```

In browser, log in, then open DevTools → Console and run:
```js
fetch('/api/keys').then(r => r.json()).then(console.log)
```

Expected: `[]` (empty array, since DB is empty).

**Step 3: Test POST via console**

```js
fetch('/api/keys', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'Test Key', model: 'GPT-4', tags: ['test'] })
}).then(r => r.json()).then(console.log)
```

Expected: object with `id`, `key` (full `sk_live_...`), `key_prefix`, `key_suffix`, `name`, `model`, etc.

**Step 4: Verify the key appears in Supabase**

Supabase Dashboard → Table Editor → `api_keys`. Should see 1 row.

**Step 5: Commit**

```bash
git add app/api/keys/route.ts
git commit -m "feat: add GET and POST /api/keys route"
```

---

### Task 5: Create DELETE /api/keys/[id] route

**Files:**
- Create: `app/api/keys/[id]/route.ts`

**Step 1: Create the route handler**

Create `app/api/keys/[id]/route.ts`:

```ts
import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { userId } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { id } = await params

  const { error } = await supabase
    .from('api_keys')
    .delete()
    .eq('id', id)
    .eq('user_id', userId) // scoped to user — can't delete another user's key

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return new NextResponse(null, { status: 204 })
}
```

**Step 2: Test DELETE via browser console**

First get the id from the GET test above, then:
```js
// Replace <id> with the UUID from the GET response
fetch('/api/keys/<id>', { method: 'DELETE' }).then(r => console.log(r.status))
```

Expected: `204`

Verify the row is gone in Supabase Table Editor.

**Step 3: Commit**

```bash
git add app/api/keys/[id]/route.ts
git commit -m "feat: add DELETE /api/keys/[id] route"
```

---

### Task 6: Create POST /api/keys/[id]/rotate route

**Files:**
- Create: `app/api/keys/[id]/rotate/route.ts`

**Step 1: Create the route handler**

Create `app/api/keys/[id]/rotate/route.ts`:

```ts
import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import crypto from 'crypto'

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { userId } = await auth()
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { id } = await params

  const raw = crypto.randomBytes(16).toString('hex')
  const key = `sk_live_${raw}`

  const { data, error } = await supabase
    .from('api_keys')
    .update({
      key,
      key_prefix: 'sk_live_',
      key_suffix: raw.slice(-4),
    })
    .eq('id', id)
    .eq('user_id', userId) // scoped to user
    .select('id, name, key_prefix, key_suffix, model, tags, requests, cost, status, created_at, last_used')
    .single()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  // Full key returned once only
  return NextResponse.json({ ...data, key })
}
```

**Step 2: Test via browser console (create a fresh key first)**

```js
// First create a key and grab its id
const { id } = await fetch('/api/keys', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'Rotate Test', model: 'Claude', tags: [] })
}).then(r => r.json())

// Then rotate it
fetch(`/api/keys/${id}/rotate`, { method: 'POST' }).then(r => r.json()).then(console.log)
```

Expected: same metadata, new `key` value starting with `sk_live_`.

**Step 3: Commit**

```bash
git add app/api/keys/[id]/rotate/route.ts
git commit -m "feat: add POST /api/keys/[id]/rotate route"
```

---

### Task 7: Refactor api-keys-page.tsx to use API routes

**Files:**
- Modify: `components/api-keys-page.tsx`

This is a full rewrite of the component. Replace the entire file with the following.

Key changes from the current version:
- `ApiKey` interface uses snake_case to match DB columns, no `key` field in list state
- State initializes empty, `useEffect` fetches on mount
- `handleAddKey` calls POST, shows one-time reveal dialog
- `handleRevoke` calls DELETE
- Rotate menu item calls the rotate endpoint, shows one-time reveal dialog
- `maskedKey` is computed from `key_prefix + '****' + key_suffix`

**Step 1: Replace the file**

```tsx
'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { MoreHorizontal, Plus, Copy, Trash2, RotateCw } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface ApiKey {
  id: string
  name: string
  key_prefix: string
  key_suffix: string
  model: string
  tags: string[]
  cost: number
  requests: number
  created_at: string
  last_used: string | null
  status: 'active' | 'inactive'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatLastUsed(iso: string | null) {
  if (!iso) return 'Never'
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`
  return `${Math.floor(hours / 24)} day${Math.floor(hours / 24) !== 1 ? 's' : ''} ago`
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Create dialog state
  const [createOpen, setCreateOpen] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyModel, setNewKeyModel] = useState('')
  const [newKeyTags, setNewKeyTags] = useState('')
  const [creating, setCreating] = useState(false)

  // One-time reveal dialog state
  const [revealKey, setRevealKey] = useState<string | null>(null)
  const [revealOpen, setRevealOpen] = useState(false)

  useEffect(() => {
    fetch('/api/keys')
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load keys')
        return r.json()
      })
      .then(setKeys)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const handleRevoke = async (id: string) => {
    const res = await fetch(`/api/keys/${id}`, { method: 'DELETE' })
    if (res.ok) {
      setKeys((prev) => prev.filter((k) => k.id !== id))
    }
  }

  const handleRotate = async (id: string) => {
    const res = await fetch(`/api/keys/${id}/rotate`, { method: 'POST' })
    if (!res.ok) return
    const data = await res.json()
    // Update the key in the list (new suffix)
    setKeys((prev) => prev.map((k) => (k.id === id ? { ...data } : k)))
    // Show the full key one time
    setRevealKey(data.key)
    setRevealOpen(true)
  }

  const handleAddKey = async () => {
    if (!newKeyName || !newKeyModel) return
    setCreating(true)

    const tags = newKeyTags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)

    const res = await fetch('/api/keys', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newKeyName, model: newKeyModel, tags }),
    })

    setCreating(false)

    if (!res.ok) return

    const data = await res.json()
    // Add to list (without the full key)
    const { key, ...keyWithoutSecret } = data
    setKeys((prev) => [keyWithoutSecret, ...prev])
    setCreateOpen(false)
    setNewKeyName('')
    setNewKeyModel('')
    setNewKeyTags('')
    // Show the full key one time
    setRevealKey(key)
    setRevealOpen(true)
  }

  return (
    <div className="p-8">
      {/* One-time key reveal dialog */}
      <Dialog open={revealOpen} onOpenChange={setRevealOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save your API key</DialogTitle>
            <DialogDescription>
              This is the only time your full API key will be shown. Copy it now and store it
              somewhere safe.
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-center gap-2 p-3 bg-secondary rounded-md">
            <code className="text-xs text-accent flex-1 break-all">{revealKey}</code>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => revealKey && handleCopy(revealKey)}
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
          <DialogFooter>
            <Button onClick={() => setRevealOpen(false)}>I&apos;ve saved it</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-foreground mb-2">API Keys</h2>
          <p className="text-muted-foreground">
            Manage and monitor your API keys with tagging and cost tracking
          </p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 bg-primary hover:bg-primary text-primary-foreground">
              <Plus className="w-4 h-4" />
              New Key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
              <DialogDescription>
                Generate a new API key for a specific model. Add tags to organize your keys.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Key Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., Production API Key"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="model">Model</Label>
                <Select value={newKeyModel} onValueChange={setNewKeyModel}>
                  <SelectTrigger id="model">
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Gemma 27B">Gemma 27B</SelectItem>
                    <SelectItem value="Claude-Opus-4.5">Claude-Opus-4.5</SelectItem>
                    <SelectItem value="GPT-4">GPT-4</SelectItem>
                    <SelectItem value="GPT-3.5">GPT-3.5</SelectItem>
                    <SelectItem value="Claude">Claude</SelectItem>
                    <SelectItem value="Claude-3-Opus">Claude 3 Opus</SelectItem>
                    <SelectItem value="Claude-3-Sonnet">Claude 3 Sonnet</SelectItem>
                    <SelectItem value="Gemini-3-Pro">Gemini-3-Pro</SelectItem>
                    <SelectItem value="Llama-2">Llama 2</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="tags">Tags</Label>
                <Input
                  id="tags"
                  placeholder="e.g., production, critical (comma-separated)"
                  value={newKeyTags}
                  onChange={(e) => setNewKeyTags(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddKey} disabled={creating}>
                {creating ? 'Creating...' : 'Create Key'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card className="bg-card border-border p-4">
          <p className="text-muted-foreground text-sm mb-1">Active Keys</p>
          <p className="text-2xl font-bold text-foreground">{keys.length}</p>
        </Card>
        <Card className="bg-card border-border p-4">
          <p className="text-muted-foreground text-sm mb-1">Total Requests</p>
          <p className="text-2xl font-bold text-foreground">
            {keys.reduce((sum, k) => sum + k.requests, 0).toLocaleString()}
          </p>
        </Card>
        <Card className="bg-card border-border p-4">
          <p className="text-muted-foreground text-sm mb-1">Total Cost</p>
          <p className="text-2xl font-bold text-foreground">
            ${keys.reduce((sum, k) => sum + k.cost, 0).toLocaleString()}
          </p>
        </Card>
      </div>

      {/* Keys Table */}
      <Card className="bg-card border-border overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">Loading...</div>
        ) : error ? (
          <div className="p-8 text-center text-destructive">{error}</div>
        ) : keys.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No API keys yet. Create one to get started.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary bg-opacity-50">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Key Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Key ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Tags
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Requests
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Last Used
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {keys.map((key) => (
                  <tr
                    key={key.id}
                    className="border-b border-border hover:bg-secondary hover:bg-opacity-30 transition"
                  >
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-foreground">{key.name}</p>
                        <p className="text-xs text-muted-foreground">
                          Created {formatDate(key.created_at)}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <code className="text-xs bg-secondary bg-opacity-50 px-2 py-1 rounded text-accent">
                        {key.key_prefix}****{key.key_suffix}
                      </code>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-block bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs font-medium">
                        {key.model}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-1 flex-wrap">
                        {key.tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-block bg-purple-500/20 text-purple-400 px-2 py-1 rounded text-xs font-medium"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-foreground">{key.requests.toLocaleString()}</td>
                    <td className="px-6 py-4 text-foreground">${key.cost.toLocaleString()}</td>
                    <td className="px-6 py-4 text-muted-foreground text-xs">
                      {formatLastUsed(key.last_used)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-muted-foreground hover:text-foreground"
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-card border-border">
                          <DropdownMenuItem
                            className="text-foreground cursor-pointer hover:bg-secondary"
                            onClick={() => handleRotate(key.id)}
                          >
                            <RotateCw className="w-4 h-4 mr-2" />
                            Rotate
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive cursor-pointer hover:bg-secondary"
                            onClick={() => handleRevoke(key.id)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Revoke
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
```

**Step 2: Check TypeScript compiles**

```bash
npx tsc --noEmit
```

Expected: no errors.

**Step 3: Verify in the browser**

With `npm run dev` running:
1. Log in and navigate to the API Keys page
2. Click "New Key" → fill in name/model/tags → click "Create Key"
3. The one-time reveal dialog appears with the full `sk_live_...` key
4. Click "I've saved it" — key disappears, table shows the new entry with masked key
5. Open the row's dropdown → click "Rotate" → reveal dialog appears with new key
6. Click "Revoke" → row disappears from table
7. Verify Supabase Table Editor reflects all these changes

**Step 4: Commit**

```bash
git add components/api-keys-page.tsx
git commit -m "feat: wire api-keys-page to Supabase via API routes"
```

---

### Task 8: Update .gitignore for migration files (optional safety check)

**Files:**
- Modify: `.gitignore`

**Step 1: Verify .env.local is already ignored**

```bash
grep ".env.local" .gitignore
```

Expected: `.env.local` is listed (it should be — Next.js scaffolds this).

**Step 2: Commit the migration file**

```bash
git add supabase/
git commit -m "feat: add supabase migrations directory"
```

---

## Done

All 8 tasks complete. The API keys page now reads/writes to Supabase, keys are scoped per Clerk user, full key is revealed exactly once, and all key generation uses server-side crypto with 128-bit entropy.
