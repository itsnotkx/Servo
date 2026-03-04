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
