'use client'

import { Fragment, useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronRight, Trash2 } from 'lucide-react'

interface ModelUsageEntry {
  requests: number
  input_tokens: number
  output_tokens: number
  cost: number
}

interface Chunk {
  subtask_id: string
  subtask_text: string
  complexity_id: string
  model: string
  latency_ms: number
  input_tokens: number
  output_tokens: number
  cost: number
  cost_savings: number
  depends_on: string[]
}

interface ExecutionLog {
  id: string
  key_id: string
  created_at: string
  prompt_preview: string | null
  subtask_count: number
  total_input_tokens: number
  total_output_tokens: number
  total_latency_ms: number | null
  total_cost: number
  total_savings: number
  model_usage: Record<string, ModelUsageEntry> | null
  chunks: Chunk[] | null
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function ComplexityBadge({ id }: { id: string }) {
  const isSimple = id === 'simple'
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
        isSimple ? 'bg-green-500/20 text-green-400' : 'bg-orange-500/20 text-orange-400'
      }`}
    >
      {id}
    </span>
  )
}

function ExpandedDetail({ log }: { log: ExecutionLog }) {
  return (
    <tr>
      <td colSpan={11} className="border-b border-border bg-secondary/30 px-5 py-5">
        <div className="mb-5">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Full Prompt
          </p>
          <p className="rounded-lg border border-border bg-background p-3 text-sm text-foreground whitespace-pre-wrap break-words">
            {log.prompt_preview ?? <span className="italic text-muted-foreground">No prompt recorded</span>}
          </p>
        </div>

        {log.chunks && log.chunks.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Subtask Breakdown
            </p>
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-secondary/60">
                    <th className="w-8 px-3 py-2 text-left font-medium text-muted-foreground">#</th>
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">Subtask</th>
                    <th className="w-20 px-3 py-2 text-left font-medium text-muted-foreground">Complexity</th>
                    <th className="w-40 px-3 py-2 text-left font-medium text-muted-foreground">Model</th>
                    <th className="w-20 px-3 py-2 text-right font-medium text-muted-foreground">In Tokens</th>
                    <th className="w-20 px-3 py-2 text-right font-medium text-muted-foreground">Out Tokens</th>
                    <th className="w-24 px-3 py-2 text-right font-medium text-muted-foreground">Latency</th>
                    <th className="w-24 px-3 py-2 text-right font-medium text-muted-foreground">Cost</th>
                    <th className="w-24 px-3 py-2 text-right font-medium text-muted-foreground">Savings</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {log.chunks.map((chunk, index) => (
                    <tr key={chunk.subtask_id} className="hover:bg-secondary/20">
                      <td className="px-3 py-2 font-mono text-muted-foreground">{index + 1}</td>
                      <td className="max-w-xs px-3 py-2 text-foreground">
                        <span className="block" title={chunk.subtask_text}>
                          {chunk.subtask_text}
                        </span>
                        {chunk.depends_on && chunk.depends_on.length > 0 && (
                          <span className="mt-0.5 block text-xs text-muted-foreground">
                            depends on: {chunk.depends_on.join(', ')}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <ComplexityBadge id={chunk.complexity_id} />
                      </td>
                      <td className="px-3 py-2 font-mono text-blue-400">{chunk.model}</td>
                      <td className="px-3 py-2 text-right font-mono text-foreground">
                        {chunk.input_tokens.toLocaleString()}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-foreground">
                        {chunk.output_tokens.toLocaleString()}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-muted-foreground">
                        {chunk.latency_ms.toLocaleString()} ms
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-foreground">
                        ${chunk.cost.toFixed(6)}
                      </td>
                      <td className="px-3 py-2 text-right font-mono">
                        <span
                          className={
                            chunk.cost_savings > 0 ? 'font-medium text-accent' : 'text-muted-foreground'
                          }
                        >
                          ${chunk.cost_savings.toFixed(6)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-border bg-secondary/40 font-semibold">
                    <td className="px-3 py-2" />
                    <td className="px-3 py-2 text-xs text-muted-foreground">Total</td>
                    <td className="px-3 py-2" />
                    <td className="px-3 py-2" />
                    <td className="px-3 py-2 text-right font-mono text-foreground">
                      {log.total_input_tokens.toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-foreground">
                      {log.total_output_tokens.toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-muted-foreground">
                      {(log.total_latency_ms ?? 0).toLocaleString()} ms
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-foreground">
                      ${log.total_cost.toFixed(6)}
                    </td>
                    <td className="px-3 py-2 text-right font-mono">
                      <span
                        className={log.total_savings > 0 ? 'font-medium text-accent' : 'text-muted-foreground'}
                      >
                        ${log.total_savings.toFixed(6)}
                      </span>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}
      </td>
    </tr>
  )
}

export default function ExecutionLogsPage() {
  const [logs, setLogs] = useState<ExecutionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  async function loadLogs() {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/logs')
      if (!response.ok) {
        throw new Error('Failed to load logs')
      }
      const data = await response.json()
      setLogs(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load logs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadLogs()
  }, [])

  function toggleRow(id: string) {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  async function handleDelete(logId: string) {
    setDeletingId(logId)
    setError(null)
    try {
      const response = await fetch(`/api/logs/${logId}`, { method: 'DELETE' })
      if (!response.ok) {
        throw new Error('Failed to delete log')
      }
      setLogs((prev) => prev.filter((log) => log.id !== logId))
      setExpandedId((prev) => (prev === logId ? null : prev))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete log')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-bold text-foreground">Execution Logs</h2>
        <p className="text-muted-foreground">
          Per-request telemetry. Click a row to inspect its prompt and subtask breakdown.
        </p>
      </div>

      <Card className="overflow-hidden border-border bg-card">
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
                  <th className="w-8 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground" />
                  <th className="w-36 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Time
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Prompt
                  </th>
                  <th className="w-24 px-5 py-3 text-center text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Subtasks
                  </th>
                  <th className="w-28 px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    In Tokens
                  </th>
                  <th className="w-28 px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Out Tokens
                  </th>
                  <th className="w-28 px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Latency
                  </th>
                  <th className="w-28 px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Cost
                  </th>
                  <th className="w-28 px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Savings
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Models
                  </th>
                  <th className="w-20 px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Delete
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {logs.map((log) => {
                  const isExpanded = expandedId === log.id
                  const hasDetail = Boolean(log.prompt_preview) || Boolean(log.chunks && log.chunks.length > 0)

                  return (
                    <Fragment key={log.id}>
                      <tr
                        onClick={() => hasDetail && toggleRow(log.id)}
                        className={`transition-colors ${
                          hasDetail ? 'cursor-pointer hover:bg-secondary/20' : ''
                        } ${isExpanded ? 'bg-secondary/20' : ''}`}
                      >
                        <td className="px-3 py-4 text-muted-foreground">
                          {hasDetail ? (
                            isExpanded ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )
                          ) : null}
                        </td>
                        <td className="px-5 py-4 text-xs whitespace-nowrap text-muted-foreground">
                          {formatDate(log.created_at)}
                        </td>
                        <td className="px-5 py-4 text-foreground">
                          <span className="block max-w-[220px] truncate" title={log.prompt_preview ?? ''}>
                            {log.prompt_preview ?? <span className="text-muted-foreground">-</span>}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-center">
                          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-xs font-medium text-foreground">
                            {log.subtask_count}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-xs text-foreground">
                          {log.total_input_tokens.toLocaleString()}
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-xs text-foreground">
                          {log.total_output_tokens.toLocaleString()}
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-xs whitespace-nowrap text-muted-foreground">
                          {(log.total_latency_ms ?? 0).toLocaleString()} ms
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-xs whitespace-nowrap text-foreground">
                          ${log.total_cost.toFixed(6)}
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-xs whitespace-nowrap">
                          <span className={log.total_savings > 0 ? 'font-medium text-accent' : 'text-muted-foreground'}>
                            ${log.total_savings.toFixed(6)}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex flex-wrap gap-1">
                            {log.model_usage && Object.keys(log.model_usage).length > 0 ? (
                              Object.entries(log.model_usage).map(([model, usage]) => (
                                <span
                                  key={model}
                                  className="inline-block rounded-full bg-blue-500/20 px-2 py-0.5 text-xs whitespace-nowrap text-blue-400"
                                >
                                  {model} x{usage.requests}
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-muted-foreground">-</span>
                            )}
                          </div>
                        </td>
                        <td className="px-5 py-4 text-right">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                            disabled={deletingId === log.id}
                            onClick={(event) => {
                              event.stopPropagation()
                              void handleDelete(log.id)
                            }}
                            aria-label="Delete execution log"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                      {isExpanded && <ExpandedDetail log={log} />}
                    </Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
