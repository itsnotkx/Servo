'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'

interface ExecutionLog {
  id: string
  key_id: string
  created_at: string
  prompt_preview: string | null
  subtask_count: number
  total_input_tokens: number
  total_output_tokens: number
  total_latency_ms: number
  total_cost: number
  total_savings: number
  model_usage: Record<string, number> | null
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function ExecutionLogsPage() {
  const [logs, setLogs] = useState<ExecutionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/logs')
      .then(r => { if (!r.ok) throw new Error('Failed to load logs'); return r.json() })
      .then(setLogs)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground mb-2">Execution Logs</h2>
        <p className="text-muted-foreground">Per-request telemetry — tokens, cost, and savings</p>
      </div>

      <Card className="bg-card border-border overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">Loading...</div>
        ) : error ? (
          <div className="p-8 text-center text-destructive">{error}</div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">No executions logged yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-secondary/50">
                  <th className="px-5 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider w-36">Time</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Prompt</th>
                  <th className="px-5 py-3 text-center text-xs font-semibold text-muted-foreground uppercase tracking-wider w-24">Subtasks</th>
                  <th className="px-5 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider w-28">In Tokens</th>
                  <th className="px-5 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider w-28">Out Tokens</th>
                  <th className="px-5 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider w-28">Latency</th>
                  <th className="px-5 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider w-28">Cost</th>
                  <th className="px-5 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider w-28">Savings</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Models</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {logs.map(log => (
                  <tr key={log.id} className="hover:bg-secondary/20 transition-colors">
                    <td className="px-5 py-4 text-muted-foreground text-xs whitespace-nowrap">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-5 py-4 text-foreground">
                      <span className="block max-w-[220px] truncate" title={log.prompt_preview ?? ''}>
                        {log.prompt_preview ?? <span className="text-muted-foreground">—</span>}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-center">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-secondary text-foreground text-xs font-medium">
                        {log.subtask_count}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right font-mono text-xs text-foreground">
                      {log.total_input_tokens.toLocaleString()}
                    </td>
                    <td className="px-5 py-4 text-right font-mono text-xs text-foreground">
                      {log.total_output_tokens.toLocaleString()}
                    </td>
                    <td className="px-5 py-4 text-right font-mono text-xs text-muted-foreground whitespace-nowrap">
                      {log.total_latency_ms.toLocaleString()} ms
                    </td>
                    <td className="px-5 py-4 text-right font-mono text-xs text-foreground whitespace-nowrap">
                      ${log.total_cost.toFixed(6)}
                    </td>
                    <td className="px-5 py-4 text-right font-mono text-xs whitespace-nowrap">
                      <span className={log.total_savings > 0 ? 'text-accent font-medium' : 'text-muted-foreground'}>
                        ${log.total_savings.toFixed(6)}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex gap-1 flex-wrap">
                        {log.model_usage && Object.keys(log.model_usage).length > 0
                          ? Object.entries(log.model_usage).map(([model, count]) => (
                              <span key={model} className="inline-block bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full text-xs whitespace-nowrap">
                                {model} ×{count}
                              </span>
                            ))
                          : <span className="text-muted-foreground text-xs">—</span>}
                      </div>
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
