'use client'

import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { CreditCard, Receipt, TrendingDown, Zap } from 'lucide-react'

interface ExecutionLog {
  id: string
  created_at: string
  prompt_preview: string | null
  total_cost: number
  total_savings: number
}

function formatMonth(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short' })
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function BillingPage() {
  const [logs, setLogs] = useState<ExecutionLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/logs')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Failed to load billing data')
        }
        return response.json()
      })
      .then((data) => setLogs(Array.isArray(data) ? data : []))
      .catch(() => setLogs([]))
      .finally(() => setLoading(false))
  }, [])

  const totalCost = logs.reduce((sum, log) => sum + (log.total_cost ?? 0), 0)
  const totalSavings = logs.reduce((sum, log) => sum + (log.total_savings ?? 0), 0)
  const promptCount = logs.length
  const averagePromptCost = promptCount > 0 ? totalCost / promptCount : 0

  const monthlyTotals = new Map<string, { month: string; cost: number; savings: number }>()
  for (const log of logs) {
    const date = new Date(log.created_at)
    const key = `${date.getFullYear()}-${date.getMonth()}`
    const existing = monthlyTotals.get(key) ?? {
      month: formatMonth(log.created_at),
      cost: 0,
      savings: 0,
    }
    existing.cost += log.total_cost ?? 0
    existing.savings += log.total_savings ?? 0
    monthlyTotals.set(key, existing)
  }

  const monthlyData = Array.from(monthlyTotals.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-6)
    .map(([, value]) => ({
      month: value.month,
      cost: Number(value.cost.toFixed(6)),
      savings: Number(value.savings.toFixed(6)),
    }))

  const recentPromptCharges = logs.slice(0, 10)

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-bold text-foreground">Billing</h2>
        <p className="text-muted-foreground">Prompt-level cost and savings recorded by the Servo SDK</p>
      </div>

      <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border bg-card p-6">
          <p className="mb-1 text-sm text-muted-foreground">Total Spend</p>
          <p className="text-2xl font-bold text-foreground">
            {loading ? '...' : `$${totalCost.toFixed(6)}`}
          </p>
        </Card>

        <Card className="border-border bg-card p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="mb-1 text-sm text-muted-foreground">Total Saved</p>
              <p className="text-2xl font-bold text-accent">
                {loading ? '...' : `$${totalSavings.toFixed(6)}`}
              </p>
            </div>
            <TrendingDown className="h-5 w-5 text-accent" />
          </div>
        </Card>

        <Card className="border-border bg-card p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="mb-1 text-sm text-muted-foreground">Prompt Count</p>
              <p className="text-2xl font-bold text-foreground">
                {loading ? '...' : promptCount.toLocaleString()}
              </p>
            </div>
            <Receipt className="h-5 w-5 text-primary" />
          </div>
        </Card>

        <Card className="border-border bg-card p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="mb-1 text-sm text-muted-foreground">Average Prompt Cost</p>
              <p className="text-2xl font-bold text-foreground">
                {loading ? '...' : `$${averagePromptCost.toFixed(6)}`}
              </p>
            </div>
            <Zap className="h-5 w-5 text-destructive" />
          </div>
        </Card>
      </div>

      <Card className="mb-8 border-border bg-card p-6">
        <h3 className="mb-4 text-lg font-semibold text-foreground">Monthly Prompt Spending</h3>
        {loading ? (
          <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
            Loading...
          </div>
        ) : monthlyData.length === 0 ? (
          <div className="flex h-[300px] items-center justify-center text-sm text-muted-foreground">
            No billing data yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
              <XAxis dataKey="month" stroke="#a0aec0" style={{ fontSize: '12px' }} />
              <YAxis stroke="#a0aec0" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1f26',
                  border: '1px solid #2d3748',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#e4e6eb' }}
              />
              <Bar dataKey="cost" fill="#ef4444" name="Spend" radius={[8, 8, 0, 0]} />
              <Bar dataKey="savings" fill="#0ea5e9" name="Savings" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="border-border bg-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-foreground">Payment Method</h3>
            <CreditCard className="h-5 w-5 text-primary" />
          </div>
          <div className="relative mb-4 overflow-hidden rounded-lg bg-gradient-to-br from-primary to-accent p-6 text-white">
            <div className="absolute right-0 top-0 -mr-8 -mt-8 h-20 w-20 rounded-full bg-white opacity-10" />
            <p className="mb-2 text-sm">Demo Payment Method</p>
            <p className="text-2xl font-bold tracking-widest">•••• 4242</p>
            <p className="mt-4 text-xs">Usage-based billing from recorded prompt costs</p>
          </div>
          <p className="text-sm text-muted-foreground">
            This page now reflects prompt costs recorded by the SDK instead of placeholder subscription data.
          </p>
        </Card>

        <div className="lg:col-span-2">
          <Card className="border-border bg-card p-6">
            <h3 className="mb-4 text-lg font-semibold text-foreground">Recent Prompt Charges</h3>
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading...</p>
            ) : recentPromptCharges.length === 0 ? (
              <p className="text-sm text-muted-foreground">No prompt charges recorded yet.</p>
            ) : (
              <div className="space-y-3">
                {recentPromptCharges.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-center justify-between rounded-lg bg-secondary/50 p-3 transition hover:bg-secondary/70"
                  >
                    <div className="min-w-0 flex-1 pr-4">
                      <p className="truncate font-medium text-foreground">
                        {log.prompt_preview || 'Untitled prompt'}
                      </p>
                      <p className="text-xs text-muted-foreground">{formatDateTime(log.created_at)}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-foreground">${log.total_cost.toFixed(6)}</p>
                      <p className="text-xs text-accent">Saved ${log.total_savings.toFixed(6)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
