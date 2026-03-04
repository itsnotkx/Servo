# Routing Tab Design

## Overview

Add a "Routing" tab to the Servo dashboard where users configure how incoming prompts are classified and routed to different AI models based on complexity tiers.

Servo uses a pre-classifier model (Qwen3-14B via Outlines) to analyze each incoming prompt and assign it to a user-defined complexity tier (e.g., Simple, Complex). Each tier maps to a specific model endpoint. The classifier decides which tier to use based on the natural language `description` field of each tier.

## Architecture

### How routing works

1. Incoming prompt → pre-classifier model
2. Classifier reads all tier descriptions and picks the best-fit tier (lowest complexity that can handle the request)
3. Prompt forwarded to the model assigned to that tier
4. Default tier used as fallback when confidence is low

### What the frontend controls

The frontend lets users define `UserClassificationProfile` — the per-user config currently hardcoded in `inference/configs/user_classification_profiles.py`. Saving from the UI will persist this to Supabase and eventually replace the hardcoded profiles.

## UI Design

ReactFlow-based flow diagram:

```
┌─────────────┐        ┌──────────────────────────────┐
│  CLASSIFIER │───────▶│ Tier: Simple                 │
│  (Qwen3-14B)│   │    │ Description: [textarea]      │
└─────────────┘   │    │ Model: [dropdown] ⭐ default  │
                  │    └──────────────────────────────┘
                  │    ┌──────────────────────────────┐
                  └───▶│ Tier: Complex                │
                       │ Description: [textarea]      │
                       │ Model: [dropdown]             │
                       └──────────────────────────────┘
                              [+ Add Tier]
```

### Node types

- **Classifier node** — read-only, shows pre-classifier model name, left side of canvas
- **Tier node** — editable name, editable description textarea, model dropdown, optional ⭐ default badge

### Edges

Auto-drawn from classifier node → each tier node. Not manually repositionable by the user (layout is managed programmatically).

### Model dropdown

Populated from the user's active API keys (`/api/keys`). Only models with at least one active key are shown.

### Default tier

One tier is marked as default (⭐). It cannot be deleted. Clicking "Set as default" on any tier reassigns the default.

### Add / remove tiers

- "Add Tier" button (below the flow) adds a new blank tier node
- Tier nodes have a delete button; default tier delete is disabled

### Save

Top-right "Save" button. Sends PUT to `/api/routing`. On success, shows a brief success toast.

## Data Model

### JSON saved to DB

```json
{
  "default_category_id": "simple",
  "categories": [
    {
      "id": "simple",
      "name": "Simple",
      "description": "Use for direct, bounded tasks: factual Q&A...",
      "model": "Gemma 27B"
    },
    {
      "id": "complex",
      "name": "Complex",
      "description": "Use only when the task genuinely requires deeper reasoning...",
      "model": "Claude-Opus-4.5"
    }
  ]
}
```

`id` is auto-generated from name (slugified) on creation and stable thereafter.

### Supabase table: `routing_configs`

| column | type | notes |
|---|---|---|
| id | uuid | PK, default gen_random_uuid() |
| user_id | text | Clerk user ID, unique |
| config | jsonb | the routing config JSON |
| updated_at | timestamptz | default now() |

Upsert on `user_id` — one config per user.

## Files

| file | purpose |
|---|---|
| `components/routing-page.tsx` | Main page, ReactFlow canvas, Save button |
| `components/nodes/classifier-node.tsx` | Read-only classifier input node |
| `components/nodes/tier-node.tsx` | Editable tier node (name, description, model, default) |
| `app/api/routing/route.ts` | GET + PUT routing config |
| `components/sidebar.tsx` | Add "Routing" nav item |
| `components/dashboard-content.tsx` | Add routing page render case |

## Dependencies

- `@xyflow/react` (ReactFlow v12) — flow diagram library
