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
import type { TierNodeData, Category } from './nodes/tier-node'

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
  handlers: Pick<TierNodeData, 'onUpdate' | 'onSetDefault' | 'onDelete'>,
  existingPositions: Map<string, { x: number; y: number }>
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
    // Preserve user-dragged position; fall back to default layout for new nodes
    position: existingPositions.get(cat.id) ?? { x: 350, y: i * 180 },
    dragHandle: '.tier-drag-handle',
    data: {
      ...cat,
      isDefault: cat.id === config.default_category_id,
      availableModels,
      ...handlers,
    } satisfies TierNodeData,
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
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [loadError, setLoadError] = useState(false)

  // Stable handlers — use functional setConfig so they never go stale
  const handleUpdate = useCallback((id: string, field: keyof Category, value: string) => {
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
    ])
      .then(([routingConfig, keys]) => {
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
      .catch(() => setLoadError(true))
  }, [])

  // Rebuild ReactFlow nodes/edges whenever config or models change,
  // preserving any positions the user has dragged nodes to.
  useEffect(() => {
    if (!config) return
    setNodes((existing) => {
      const existingPositions = new Map(existing.map((n) => [n.id, n.position]))
      return buildNodes(
        config,
        availableModels,
        { onUpdate: handleUpdate, onSetDefault: handleSetDefault, onDelete: handleDelete },
        existingPositions
      )
    })
    setEdges(buildEdges(config.categories))
  }, [config, availableModels, setNodes, setEdges, handleUpdate, handleSetDefault, handleDelete])

  const handleAddTier = useCallback(() => {
    const id = `tier-${Date.now()}`
    setConfig((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        categories: [...prev.categories, { id, name: 'New Tier', description: '', model: '' }],
      }
    })
  }, [])

  const handleSave = useCallback(async () => {
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
  }, [config])

  if (loadError) {
    return (
      <div className="flex-1 flex items-center justify-center text-destructive">
        Failed to load routing config. Please refresh the page.
      </div>
    )
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
          nodesConnectable={false}
          edgesReconnectable={false}
          selectionOnDrag={false}
        >
          <Background color="hsl(var(--border))" />
          <Controls className="!bg-card !border-border [&>button]:!bg-card [&>button]:!border-border [&>button]:!text-foreground" />
        </ReactFlow>
      </div>
    </div>
  )
}
