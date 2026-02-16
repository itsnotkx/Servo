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
  key: string
  maskedKey: string
  model: string
  tags: string[]
  cost: number
  requests: number
  createdAt: string
  lastUsed: string
  status: 'active' | 'inactive'
}

const apiKeys: ApiKey[] = [
  {
    id: '1',
    name: 'Production API Key',
    key: 'sk_live_abc123def456',
    maskedKey: 'sk_live_****6',
    model: 'GPT-4',
    tags: ['production', 'critical'],
    cost: 1240,
    requests: 2800,
    createdAt: 'Dec 15, 2024',
    lastUsed: '2 minutes ago',
    status: 'active',
  },
  {
    id: '2',
    name: 'Development API Key',
    key: 'sk_test_xyz789uvw123',
    maskedKey: 'sk_test_****3',
    model: 'GPT-3.5',
    tags: ['development'],
    cost: 340,
    requests: 1200,
    createdAt: 'Jan 8, 2025',
    lastUsed: '5 hours ago',
    status: 'active',
  },
  {
    id: '3',
    name: 'Staging API Key',
    key: 'sk_stage_qwe456rty789',
    maskedKey: 'sk_stage_***9',
    model: 'Claude',
    tags: ['staging', 'testing'],
    cost: 120,
    requests: 600,
    createdAt: 'Jan 10, 2025',
    lastUsed: '1 day ago',
    status: 'active',
  },
]

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>(() => {
    // Initialize from localStorage if available
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('apiKeys')
      if (saved) {
        try {
          return JSON.parse(saved)
        } catch (e) {
          console.error('Failed to parse saved keys:', e)
        }
      }
    }
    return apiKeys
  })
  const [open, setOpen] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyModel, setNewKeyModel] = useState('')
  const [newKeyTags, setNewKeyTags] = useState('')

  // Save to localStorage whenever keys change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('apiKeys', JSON.stringify(keys))
    }
  }, [keys])

  const handleCopy = (key: string) => {
    navigator.clipboard.writeText(key)
    // Could add toast notification here
  }

  const handleRevoke = (id: string) => {
    setKeys(keys.filter((k) => k.id !== id))
  }

  const handleAddKey = () => {
    if (!newKeyName || !newKeyModel) {
      return
    }

    const generatedKey = `sk_${newKeyModel.toLowerCase().replace(/[^a-z0-9]/g, '')}_${Math.random().toString(36).substring(2, 15)}`
    const lastFour = generatedKey.slice(-4)
    
    const tags = newKeyTags
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag.length > 0)

    // Generate unique ID by finding max existing ID and adding 1
    const maxId = keys.length > 0 
      ? Math.max(...keys.map(k => parseInt(k.id) || 0))
      : 0
    
    const newKey: ApiKey = {
      id: String(maxId + 1),
      name: newKeyName,
      key: generatedKey,
      maskedKey: `${generatedKey.split('_')[0]}_${generatedKey.split('_')[1]}_****${lastFour}`,
      model: newKeyModel,
      tags,
      cost: 0,
      requests: 0,
      createdAt: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      lastUsed: 'Never',
      status: 'active',
    }

    setKeys([...keys, newKey])
    setOpen(false)
    setNewKeyName('')
    setNewKeyModel('')
    setNewKeyTags('')
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-foreground mb-2">API Keys</h2>
          <p className="text-muted-foreground">Manage and monitor your API keys with tagging and cost tracking</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
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
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddKey}>Create Key</Button>
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
          <p className="text-2xl font-bold text-foreground">{keys.reduce((sum, k) => sum + k.requests, 0).toLocaleString()}</p>
        </Card>
        <Card className="bg-card border-border p-4">
          <p className="text-muted-foreground text-sm mb-1">Total Cost</p>
          <p className="text-2xl font-bold text-foreground">${keys.reduce((sum, k) => sum + k.cost, 0).toLocaleString()}</p>
        </Card>
      </div>

      {/* Keys Table */}
      <Card className="bg-card border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-secondary bg-opacity-50">
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Key Name</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Key ID</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Model</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Tags</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Requests</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Cost</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Last Used</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody>
              {keys.map((key) => (
                <tr key={key.id} className="border-b border-border hover:bg-secondary hover:bg-opacity-30 transition">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium text-foreground">{key.name}</p>
                      <p className="text-xs text-muted-foreground">Created {key.createdAt}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-secondary bg-opacity-50 px-2 py-1 rounded text-accent">{key.maskedKey}</code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCopy(key.key)}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
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
                  <td className="px-6 py-4 text-muted-foreground text-xs">{key.lastUsed}</td>
                  <td className="px-6 py-4 text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="bg-card border-border">
                        <DropdownMenuItem className="text-foreground cursor-pointer hover:bg-secondary">
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
      </Card>
    </div>
  )
}
