# Routing Tab Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Routing" tab to the Servo dashboard where users define complexity-tier routing with a ReactFlow diagram, wired to a Supabase-backed API.

**Architecture:** A ReactFlow canvas renders a read-only Classifier node on the left and editable Tier nodes on the right, auto-connected by edges. Config state lives in React, is rebuilt into ReactFlow nodes whenever it changes, and is persisted to a `routing_configs` Supabase table via a Next.js API route. The model dropdown in each tier node is populated exclusively from the user's active API keys.

**Tech Stack:** Next.js 15 App Router, `@xyflow/react` (ReactFlow v12), Supabase (jsonb upsert), Clerk auth, Tailwind CSS, shadcn/ui components.

---

### Task 1: Create Supabase `routing_configs` table

**Files:**
- No code files — SQL run in Supabase dashboard

**Step 1: Run this SQL in the Supabase dashboard SQL editor**

```sql
create table routing_configs (
  id         uuid        primary key default gen_random_uuid(),
  user_id    text        not null unique,
  config     jsonb       not null,
  updated_at timestamptz not null default now()
);
```

**Step 2: Verify**

In the Supabase Table Editor, confirm `routing_configs` appears with the four columns.

---

### Task 2: Install `@xyflow/react`

**Files:**
- Modify: `package.json` (via npm)

**Step 1: Install**

```bash
npm install @xyflow/react
```

**Step 2: Verify**

```bash
grep "@xyflow/react" package.json
```

Expected: a line like `"@xyflow/react": "^12.x.x"`

**Step 3: Commit**

```bash
git add package.json package-lock.json
git commit -m "chore: add @xyflow/react dependency"
```

---

### Task 3: Create `GET` + `PUT /api/routing` route

**Files:**
- Create: `app/api/routing/route.ts`

**Step 1: Create the file**

```typescript
// app/api/routing/route.ts
import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

const DEFAULT_CONFIG = {
  default_category_id: 'simple',
  categories: [
    {
      id: 'simple',
      name: 'Simple',
      description:
        'Use for direct, bounded tasks: factual Q&A, concise explanations, and routine coding work (e.g. implementing a single function, small bug fixes). Prefer this category whenever the request can be fully handled without deep multi-step analysis.',
      model: '',
    },
    {
      id: 'complex',
      name: 'Complex',
      description:
        'Use only when the task genuinely requires deeper reasoning: broad system design, non-trivial architecture or migration plans, advanced debugging across multiple interacting components, or nuanced tradeoff analysis. Do not use for routine single-file or single-function tasks.',
      model: '',
    },
  ],
}

export async function GET() {
  const { userId } = await auth()
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { data } = await supabase
    .from('routing_configs')
    .select('config')
    .eq('user_id', userId)
    .single()

  return NextResponse.json(data?.config ?? DEFAULT_CONFIG)
}

export async function PUT(request: Request) {
  const { userId } = await auth()
  if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const config = body as { default_category_id?: unknown; categories?: unknown }
  if (typeof config.default_category_id !== 'string' || !Array.isArray(config.categories)) {
    return NextResponse.json({ error: 'Invalid config structure' }, { status: 400 })
  }

  const { error } = await supabase
    .from('routing_configs')
    .upsert(
      { user_id: userId, config: body, updated_at: new Date().toISOString() },
      { onConflict: 'user_id' }
    )

  if (error) return NextResponse.json({ error: 'Internal server error' }, { status: 500 })

  return NextResponse.json({ ok: true })
}
```

**Step 2: Start the dev server and test GET**

```bash
npm run dev
```

Open `http://localhost:3000` in the browser, sign in, then open DevTools Network tab and navigate to any dashboard page. In the console run:

```javascript
fetch('/api/routing').then(r => r.json()).then(console.log)
```

Expected: the default config JSON object with `simple` and `complex` categories.

**Step 3: Test PUT**

In browser console:

```javascript
fetch('/api/routing', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    default_category_id: 'simple',
    categories: [{ id: 'simple', name: 'Simple', description: 'test', model: '' }]
  })
}).then(r => r.json()).then(console.log)
```

Expected: `{ ok: true }`. Then in Supabase dashboard, verify a row appears in `routing_configs`.

**Step 4: Commit**

```bash
git add app/api/routing/route.ts
git commit -m "feat: add GET/PUT /api/routing route"
```

---

### Task 4: Create the Classifier node component

**Files:**
- Create: `components/nodes/classifier-node.tsx`

**Step 1: Create the directory and file**

```tsx
// components/nodes/classifier-node.tsx
import { Handle, Position } from '@xyflow/react'
import { Cpu } from 'lucide-react'

export default function ClassifierNode() {
  return (
    <div className="bg-card border border-border rounded-lg p-4 w-48 shadow-md">
      <div className="flex items-center gap-2 mb-1">
        <Cpu className="w-4 h-4 text-accent" />
        <span className="text-sm font-semibold text-foreground">Classifier</span>
      </div>
      <p className="text-xs text-muted-foreground">Qwen3-14B</p>
      <Handle type="source" position={Position.Right} className="!bg-accent !border-border" />
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add components/nodes/classifier-node.tsx
git commit -m "feat: add ClassifierNode ReactFlow component"
```

---

### Task 5: Create the Tier node component

**Files:**
- Create: `components/nodes/tier-node.tsx`

**Step 1: Create the file**

```tsx
// components/nodes/tier-node.tsx
import { Handle, Position } from '@xyflow/react'
import { Trash2, Star } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export interface TierNodeData {
  id: string
  name: string
  description: string
  model: string
  isDefault: boolean
  availableModels: string[]
  onUpdate: (id: string, field: string, value: string) => void
  onSetDefault: (id: string) => void
  onDelete: (id: string) => void
}

export default function TierNode({ data }: { data: TierNodeData }) {
  return (
    <div
      className={`bg-card border rounded-lg p-4 w-80 shadow-md ${
        data.isDefault ? 'border-accent' : 'border-border'
      }`}
    >
      <Handle type="target" position={Position.Left} className="!bg-accent !border-border" />

      {/* Header row: name input + star + delete */}
      <div className="flex items-center gap-2 mb-3">
        <Input
          value={data.name}
          onChange={(e) => data.onUpdate(data.id, 'name', e.target.value)}
          className="h-7 text-sm font-semibold bg-transparent border-0 border-b border-border rounded-none px-0 focus-visible:ring-0 flex-1"
          placeholder="Tier name"
        />
        {data.isDefault && (
          <Star className="w-4 h-4 text-accent fill-accent shrink-0" title="Default tier" />
        )}
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive shrink-0"
          onClick={() => data.onDelete(data.id)}
          disabled={data.isDefault}
          title={data.isDefault ? 'Cannot delete the default tier' : 'Delete tier'}
        >
          <Trash2 className="w-3.5 h-3.5" />
        </Button>
      </div>

      {/* Description textarea — this IS the classifier condition */}
      <textarea
        value={data.description}
        onChange={(e) => data.onUpdate(data.id, 'description', e.target.value)}
        className="w-full text-xs text-muted-foreground bg-secondary/30 border border-border rounded p-2 resize-none mb-3 focus:outline-none focus:ring-1 focus:ring-accent"
        rows={4}
        placeholder="Describe when the classifier should route to this tier..."
      />

      {/* Model dropdown + Set default button */}
      <div className="flex items-center gap-2">
        <Select
          value={data.model || ''}
          onValueChange={(v) => data.onUpdate(data.id, 'model', v)}
        >
          <SelectTrigger className="h-7 text-xs flex-1">
            <SelectValue placeholder="Select model" />
          </SelectTrigger>
          <SelectContent>
            {data.availableModels.map((m) => (
              <SelectItem key={m} value={m} className="text-xs">
                {m}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {!data.isDefault && (
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs px-2 border-border text-muted-foreground hover:text-accent hover:border-accent bg-transparent shrink-0"
            onClick={() => data.onSetDefault(data.id)}
          >
            Set default
          </Button>
        )}
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add components/nodes/tier-node.tsx
git commit -m "feat: add TierNode ReactFlow component"
```

---

### Task 6: Create the main `RoutingPage` component

**Files:**
- Create: `components/routing-page.tsx`

**Step 1: Create the file**

```tsx
// components/routing-page.tsx
'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Button } from '@/components/ui/button'
import { Plus, Save } from 'lucide-react'
import ClassifierNode from './nodes/classifier-node'
import TierNode from './nodes/tier-node'
import type { TierNodeData } from './nodes/tier-node'

interface Category {
  id: string
  name: string
  description: string
  model: string
}

interface RoutingConfig {
  default_category_id: string
  categories: Category[]
}

// Defined outside component so ReactFlow doesn't recreate on every render
const NODE_TYPES: NodeTypes = {
  classifierNode: ClassifierNode,
  tierNode: TierNode,
}

function buildNodes(
  config: RoutingConfig,
  availableModels: string[],
  handlers: Pick<TierNodeData, 'onUpdate' | 'onSetDefault' | 'onDelete'>
): Node[] {
  const classifierY = Math.max(0, (config.categories.length * 180) / 2 - 40)

  const classifierNode: Node = {
    id: 'classifier',
    type: 'classifierNode',
    position: { x: 50, y: classifierY },
    data: {},
    draggable: false,
  }

  const tierNodes: Node[] = config.categories.map((cat, i) => ({
    id: cat.id,
    type: 'tierNode',
    position: { x: 350, y: i * 180 },
    data: {
      ...cat,
      isDefault: cat.id === config.default_category_id,
      availableModels,
      ...handlers,
    } satisfies TierNodeData,
    draggable: false,
  }))

  return [classifierNode, ...tierNodes]
}

function buildEdges(categories: Category[]): Edge[] {
  return categories.map((cat) => ({
    id: `classifier->${cat.id}`,
    source: 'classifier',
    target: cat.id,
    animated: true,
    style: { stroke: 'hsl(var(--accent))' },
  }))
}

export default function RoutingPage() {
  const [config, setConfig] = useState<RoutingConfig | null>(null)
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  // Stable handlers — use functional setConfig so they never go stale
  const handleUpdate = useCallback((id: string, field: string, value: string) => {
    setConfig((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        categories: prev.categories.map((c) => (c.id === id ? { ...c, [field]: value } : c)),
      }
    })
  }, [])

  const handleSetDefault = useCallback((id: string) => {
    setConfig((prev) => (prev ? { ...prev, default_category_id: id } : prev))
  }, [])

  const handleDelete = useCallback((id: string) => {
    setConfig((prev) => {
      if (!prev) return prev
      return { ...prev, categories: prev.categories.filter((c) => c.id !== id) }
    })
  }, [])

  // Load routing config and available models on mount
  useEffect(() => {
    Promise.all([
      fetch('/api/routing').then((r) => r.json()),
      fetch('/api/keys').then((r) => r.json()),
    ]).then(([routingConfig, keys]) => {
      setConfig(routingConfig as RoutingConfig)
      const models = [
        ...new Set(
          (keys as { model: string; status: string }[])
            .filter((k) => k.status === 'active')
            .map((k) => k.model)
        ),
      ]
      setAvailableModels(models)
    })
  }, [])

  // Rebuild ReactFlow nodes/edges whenever config or models change
  useEffect(() => {
    if (!config) return
    setNodes(
      buildNodes(config, availableModels, {
        onUpdate: handleUpdate,
        onSetDefault: handleSetDefault,
        onDelete: handleDelete,
      })
    )
    setEdges(buildEdges(config.categories))
  }, [config, availableModels, setNodes, setEdges, handleUpdate, handleSetDefault, handleDelete])

  const handleAddTier = () => {
    const id = `tier-${Date.now()}`
    setConfig((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        categories: [...prev.categories, { id, name: 'New Tier', description: '', model: '' }],
      }
    })
  }

  const handleSave = async () => {
    if (!config) return
    setSaving(true)
    setSaveError(null)
    const res = await fetch('/api/routing', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    setSaving(false)
    if (!res.ok) {
      setSaveError('Failed to save')
    } else {
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    }
  }

  if (!config) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        Loading...
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-8 pb-4 flex justify-between items-start shrink-0">
        <div>
          <h2 className="text-3xl font-bold text-foreground mb-2">Routing</h2>
          <p className="text-muted-foreground">
            Define how incoming prompts are classified and routed to models
          </p>
        </div>
        <div className="flex items-center gap-3">
          {saveError && <span className="text-xs text-destructive">{saveError}</span>}
          {saved && <span className="text-xs text-green-500">Saved!</span>}
          <Button
            onClick={handleAddTier}
            variant="outline"
            className="gap-2 border-border text-foreground hover:bg-secondary bg-transparent"
          >
            <Plus className="w-4 h-4" />
            Add Tier
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving}
            className="gap-2 bg-primary hover:bg-primary text-primary-foreground"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>

      {/* ReactFlow canvas */}
      <div className="flex-1 mx-8 mb-8 rounded-lg border border-border overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={NODE_TYPES}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="hsl(var(--border))" />
          <Controls className="!bg-card !border-border [&>button]:!bg-card [&>button]:!border-border [&>button]:!text-foreground" />
        </ReactFlow>
      </div>
    </div>
  )
}
```

**Step 2: Verify the page renders**

With `npm run dev` running, navigate to the dashboard. The page won't be linked yet (that's Task 7), but TypeScript should compile without errors:

```bash
npx tsc --noEmit
```

Expected: no errors related to `routing-page.tsx` or the node files.

**Step 3: Commit**

```bash
git add components/routing-page.tsx
git commit -m "feat: add RoutingPage with ReactFlow canvas"
```

---

### Task 7: Wire up sidebar and dashboard-content

**Files:**
- Modify: `components/sidebar.tsx`
- Modify: `components/dashboard-content.tsx`

**Step 1: Add "Routing" to the sidebar nav**

In `components/sidebar.tsx`, add the `Route` icon import and a new menu item.

Find the import line:
```typescript
import { BarChart3, CreditCard, Key, Settings } from 'lucide-react'
```

Replace with:
```typescript
import { BarChart3, CreditCard, Key, Route, Settings } from 'lucide-react'
```

Find the `menuItems` array:
```typescript
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]
```

Replace with:
```typescript
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'routing', label: 'Routing', icon: Route },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]
```

**Step 2: Add the routing page render case to dashboard-content**

In `components/dashboard-content.tsx`, add the import and render case.

Find:
```typescript
import DashboardOverview from './dashboard-overview'
import ApiKeysPage from './api-keys-page'
import BillingPage from './billing-page'
import SettingsPage from './settings-page'
```

Replace with:
```typescript
import DashboardOverview from './dashboard-overview'
import ApiKeysPage from './api-keys-page'
import BillingPage from './billing-page'
import RoutingPage from './routing-page'
import SettingsPage from './settings-page'
```

Find:
```tsx
      {page === 'api-keys' && <ApiKeysPage />}
      {page === 'billing' && <BillingPage />}
```

Replace with:
```tsx
      {page === 'api-keys' && <ApiKeysPage />}
      {page === 'routing' && <RoutingPage />}
      {page === 'billing' && <BillingPage />}
```

**Step 3: Verify end-to-end in browser**

1. Open `http://localhost:3000/dashboard`
2. Click "Routing" in the sidebar — the ReactFlow canvas should render with a Classifier node on the left and Simple/Complex tier nodes on the right, connected by animated edges
3. Edit a tier description — the textarea updates live
4. Change a model dropdown — only shows models from your active API keys
5. Click "Add Tier" — a new tier node appears on the canvas
6. Click "Save" — brief "Saved!" confirmation appears; check Supabase `routing_configs` table for the row

**Step 4: Commit**

```bash
git add components/sidebar.tsx components/dashboard-content.tsx
git commit -m "feat: add Routing tab to dashboard sidebar and content"
```

---

## Done

The routing tab is complete. The JSON saved to Supabase `routing_configs.config` matches the `UserClassificationProfile` structure consumed by `inference/configs/user_classification_profiles.py`, enabling the hardcoded profiles to be replaced with DB-backed ones in a future task.
