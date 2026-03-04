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
          <span title="Default tier" className="shrink-0">
            <Star className="w-4 h-4 text-accent fill-accent" />
          </span>
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
