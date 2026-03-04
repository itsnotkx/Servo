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
    setKeys((prev) => prev.map((k) => (k.id === id ? { ...data } : k)))
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
    const { key, ...keyWithoutSecret } = data
    setKeys((prev) => [keyWithoutSecret, ...prev])
    setCreateOpen(false)
    setNewKeyName('')
    setNewKeyModel('')
    setNewKeyTags('')
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
