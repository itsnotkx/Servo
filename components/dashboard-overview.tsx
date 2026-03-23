'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingDown, Zap, Activity } from 'lucide-react'

interface ApiKey {
  id: string
  name: string
  requests: number
  cost: number
  total_savings: number
}

interface ExecutionLog {
  id: string
  created_at: string
  total_cost: number
  total_savings: number
  model_usage: Record<string, number>
}

export default function DashboardOverview() {
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [logs, setLogs] = useState<ExecutionLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('/api/keys').then(r => r.json()),
      fetch('/api/logs').then(r => r.json()),
    ]).then(([keysData, logsData]) => {
      setKeys(Array.isArray(keysData) ? keysData : [])
      setLogs(Array.isArray(logsData) ? logsData : [])
    }).finally(() => setLoading(false))
  }, [])

  const totalCost = keys.reduce((sum, k) => sum + (k.cost ?? 0), 0)
  const totalSavings = keys.reduce((sum, k) => sum + (k.total_savings ?? 0), 0)
  const totalRequests = keys.reduce((sum, k) => sum + (k.requests ?? 0), 0)
  const optimizationRate = totalCost + totalSavings > 0
    ? (totalSavings / (totalCost + totalSavings)) * 100
    : 0

  // Build cost trend from last 10 logs (oldest first)
  const chartData = [...logs].reverse().slice(-10).map((log) => ({
    date: new Date(log.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    cost: Number((log.total_cost * 1000).toFixed(4)),
    savings: Number((log.total_savings * 1000).toFixed(4)),
  }))

  // Aggregate model usage across all logs
  const modelTotals: Record<string, number> = {}
  for (const log of logs) {
    if (log.model_usage) {
      for (const [model, count] of Object.entries(log.model_usage)) {
        modelTotals[model] = (modelTotals[model] ?? 0) + (count as number)
      }
    }
  }
  const totalModelRequests = Object.values(modelTotals).reduce((a, b) => a + b, 0)
  const modelDistribution = Object.entries(modelTotals).map(([name, count]) => ({
    name,
    requests: count,
    pct: totalModelRequests > 0 ? Math.round((count / totalModelRequests) * 100) : 0,
  }))

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground mb-2">Dashboard</h2>
        <p className="text-muted-foreground">Monitor your API costs and optimization metrics</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-muted-foreground text-sm mb-1">Total Spend</p>
              <p className="text-3xl font-bold text-foreground">
                {loading ? '...' : `$${totalCost.toFixed(6)}`}
              </p>
            </div>
            <div className="text-destructive">
              <Zap className="w-6 h-6" />
            </div>
          </div>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-muted-foreground text-sm mb-1">Total Saved</p>
              <p className="text-3xl font-bold text-accent">
                {loading ? '...' : `$${totalSavings.toFixed(6)}`}
              </p>
            </div>
            <div className="text-primary">
              <TrendingDown className="w-6 h-6" />
            </div>
          </div>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-muted-foreground text-sm mb-1">API Requests</p>
              <p className="text-3xl font-bold text-foreground">
                {loading ? '...' : totalRequests.toLocaleString()}
              </p>
            </div>
            <div className="text-primary">
              <Activity className="w-6 h-6" />
            </div>
          </div>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-muted-foreground text-sm mb-1">Savings Rate</p>
              <p className="text-3xl font-bold text-accent">
                {loading ? '...' : `${optimizationRate.toFixed(1)}%`}
              </p>
              <p className="text-xs text-muted-foreground mt-1">vs baseline model</p>
            </div>
            <div className="text-accent">
              <Zap className="w-6 h-6" />
            </div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2">
          <Card className="bg-card border-border p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Cost vs Savings (last 10 requests, ×10⁻³ $)</h3>
            {chartData.length === 0 ? (
              <div className="h-[300px] flex items-center justify-center text-muted-foreground text-sm">
                No execution data yet
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                  <XAxis dataKey="date" stroke="#a0aec0" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#a0aec0" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1f26', border: '1px solid #2d3748', borderRadius: '8px' }}
                    labelStyle={{ color: '#e4e6eb' }}
                  />
                  <Line type="monotone" dataKey="cost" stroke="#ef4444" strokeWidth={2} dot={false} name="Cost (m$)" />
                  <Line type="monotone" dataKey="savings" stroke="#0ea5e9" strokeWidth={2} dot={false} name="Savings (m$)" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Card>
        </div>

        <div>
          <Card className="bg-card border-border p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Model Usage</h3>
            {modelDistribution.length === 0 ? (
              <p className="text-muted-foreground text-sm">No data yet</p>
            ) : (
              <div className="space-y-3">
                {modelDistribution.map((m) => (
                  <div key={m.name}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-foreground truncate">{m.name}</span>
                      <span className="text-xs text-muted-foreground ml-2">{m.pct}%</span>
                    </div>
                    <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-primary to-accent" style={{ width: `${m.pct}%` }} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{m.requests.toLocaleString()} subtasks</p>
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
