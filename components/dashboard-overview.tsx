'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { TrendingDown, AlertCircle, Zap } from 'lucide-react'

const costData = [
  { date: 'Jan 1', cost: 450, optimized: 280 },
  { date: 'Jan 5', cost: 520, optimized: 310 },
  { date: 'Jan 10', cost: 680, optimized: 380 },
  { date: 'Jan 15', cost: 620, optimized: 340 },
  { date: 'Jan 20', cost: 740, optimized: 400 },
  { date: 'Jan 25', cost: 850, optimized: 420 },
  { date: 'Jan 30', cost: 920, optimized: 480 },
]

const modelDistribution = [
  { name: 'GPT-4', value: 35, requests: 1200 },
  { name: 'GPT-3.5', value: 40, requests: 2400 },
  { name: 'Claude', value: 20, requests: 800 },
  { name: 'Other', value: 5, requests: 200 },
]

// Per-key cost data
const perKeyCostData = {
  '1': [
    { date: 'Jan 1', cost: 250 },
    { date: 'Jan 5', cost: 290 },
    { date: 'Jan 10', cost: 380 },
    { date: 'Jan 15', cost: 340 },
    { date: 'Jan 20', cost: 420 },
    { date: 'Jan 25', cost: 480 },
    { date: 'Jan 30', cost: 520 },
  ],
  '2': [
    { date: 'Jan 1', cost: 120 },
    { date: 'Jan 5', cost: 140 },
    { date: 'Jan 10', cost: 180 },
    { date: 'Jan 15', cost: 160 },
    { date: 'Jan 20', cost: 190 },
    { date: 'Jan 25', cost: 220 },
    { date: 'Jan 30', cost: 240 },
  ],
  '3': [
    { date: 'Jan 1', cost: 80 },
    { date: 'Jan 5', cost: 90 },
    { date: 'Jan 10', cost: 120 },
    { date: 'Jan 15', cost: 120 },
    { date: 'Jan 20', cost: 130 },
    { date: 'Jan 25', cost: 150 },
    { date: 'Jan 30', cost: 160 },
  ],
}

// Per-model cost data
const perModelCostData = {
  'GPT-4': [
    { date: 'Jan 1', cost: 180 },
    { date: 'Jan 5', cost: 210 },
    { date: 'Jan 10', cost: 280 },
    { date: 'Jan 15', cost: 250 },
    { date: 'Jan 20', cost: 300 },
    { date: 'Jan 25', cost: 340 },
    { date: 'Jan 30', cost: 380 },
  ],
  'GPT-3.5': [
    { date: 'Jan 1', cost: 150 },
    { date: 'Jan 5', cost: 170 },
    { date: 'Jan 10', cost: 220 },
    { date: 'Jan 15', cost: 200 },
    { date: 'Jan 20', cost: 240 },
    { date: 'Jan 25', cost: 280 },
    { date: 'Jan 30', cost: 300 },
  ],
  'Claude': [
    { date: 'Jan 1', cost: 120 },
    { date: 'Jan 5', cost: 140 },
    { date: 'Jan 10', cost: 180 },
    { date: 'Jan 15', cost: 170 },
    { date: 'Jan 20', cost: 200 },
    { date: 'Jan 25', cost: 230 },
    { date: 'Jan 30', cost: 240 },
  ],
}

type ViewType = 'overall' | 'per-key' | 'per-model'

export default function DashboardOverview() {
  const [view, setView] = useState<ViewType>('overall')
  const [apiKeys, setApiKeys] = useState<any[]>([])
  const [selectedKey, setSelectedKey] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('GPT-4')

  useEffect(() => {
    // Load API keys from localStorage
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('apiKeys')
      if (saved) {
        try {
          const keys = JSON.parse(saved)
          setApiKeys(keys)
          if (keys.length > 0 && !selectedKey) {
            setSelectedKey(keys[0].id)
          }
        } catch (e) {
          console.error('Failed to parse saved keys:', e)
        }
      }
    }
  }, [])

  const getChartData = () => {
    if (view === 'overall') {
      return costData
    } else if (view === 'per-key' && selectedKey) {
      return perKeyCostData[selectedKey as keyof typeof perKeyCostData] || []
    } else if (view === 'per-model') {
      return perModelCostData[selectedModel as keyof typeof perModelCostData] || []
    }
    return costData
  }

  const availableModels = Array.from(new Set(apiKeys.map(k => k.model).filter(Boolean)))
  if (availableModels.length === 0) {
    availableModels.push('GPT-4', 'GPT-3.5', 'Claude')
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground mb-2">Dashboard</h2>
        <p className="text-muted-foreground">Monitor your API costs and optimization metrics</p>
        
        {/* View Selector */}
        <div className="flex gap-2 mt-4">
          <Button
            variant={view === 'overall' ? 'default' : 'outline'}
            onClick={() => setView('overall')}
            className="px-4"
          >
            Overall
          </Button>
          <Button
            variant={view === 'per-key' ? 'default' : 'outline'}
            onClick={() => setView('per-key')}
            className="px-4"
          >
            Per Key
          </Button>
          <Button
            variant={view === 'per-model' ? 'default' : 'outline'}
            onClick={() => setView('per-model')}
            className="px-4"
          >
            Per Model
          </Button>
        </div>

        {/* Key/Model Selector for filtered views */}
        {view === 'per-key' && apiKeys.length > 0 && (
          <div className="mt-4 flex gap-2 items-center flex-wrap">
            <span className="text-sm text-muted-foreground">Select Key:</span>
            {apiKeys.map((key) => (
              <Button
                key={key.id}
                variant={selectedKey === key.id ? 'default' : 'outline'}
                onClick={() => setSelectedKey(key.id)}
                size="sm"
              >
                {key.name}
              </Button>
            ))}
          </div>
        )}

        {view === 'per-model' && (
          <div className="mt-4 flex gap-2 items-center flex-wrap">
            <span className="text-sm text-muted-foreground">Select Model:</span>
            {availableModels.map((model) => (
              <Button
                key={model}
                variant={selectedModel === model ? 'default' : 'outline'}
                onClick={() => setSelectedModel(model)}
                size="sm"
              >
                {model}
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-muted-foreground text-sm mb-1">Monthly Spend</p>
              <p className="text-3xl font-bold text-foreground">$2,340</p>
              <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                <TrendingDown className="w-3 h-3" /> 12% from last month
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
              <p className="text-muted-foreground text-sm mb-1">Total amount saved</p>
              <p className="text-3xl font-bold text-accent">$580</p>
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
              <p className="text-3xl font-bold text-foreground">4.6K</p>
              <p className="text-xs text-muted-foreground mt-1">this month</p>
            </div>
            <div className="text-primary">
              <AlertCircle className="w-6 h-6" />
            </div>
          </div>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-muted-foreground text-sm mb-1">Optimization Rate</p>
              <p className="text-3xl font-bold text-accent">24.8%</p>
              <p className="text-xs text-accent mt-1">of requests routed</p>
            </div>
            <div className="text-accent">
              <Zap className="w-6 h-6" />
            </div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Cost Trend Chart */}
        <div className="lg:col-span-2">
          <Card className="bg-card border-border p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              {view === 'overall' && 'Cost Trend - Overall'}
              {view === 'per-key' && `Cost Trend - ${apiKeys.find(k => k.id === selectedKey)?.name || 'Select a Key'}`}
              {view === 'per-model' && `Cost Trend - ${selectedModel}`}
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={getChartData()}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                <XAxis dataKey="date" stroke="#a0aec0" style={{ fontSize: '12px' }} />
                <YAxis stroke="#a0aec0" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1f26',
                    border: '1px solid #2d3748',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#e4e6eb' }}
                />
                {view === 'overall' ? (
                  <>
                    <Line type="monotone" dataKey="cost" stroke="#ef4444" strokeWidth={2} dot={false} name="Actual Cost" />
                    <Line type="monotone" dataKey="optimized" stroke="#0ea5e9" strokeWidth={2} dot={false} name="Optimized Cost" />
                  </>
                ) : (
                  <Line type="monotone" dataKey="cost" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Cost" />
                )}
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Model Distribution */}
        <div>
          <Card className="bg-card border-border p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Model Usage</h3>
            <div className="space-y-3">
              {modelDistribution.map((model) => (
                <div key={model.name}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-foreground">{model.name}</span>
                    <span className="text-xs text-muted-foreground">{model.value}%</span>
                  </div>
                  <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary to-accent"
                      style={{ width: `${model.value}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{model.requests.toLocaleString()} requests</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Alerts */}
      <Card className="bg-card border-border p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Alerts & Recommendations</h3>
        <div className="space-y-3">
          <div className="flex gap-3 p-3 bg-secondary bg-opacity-50 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-foreground font-medium">High-cost requests detected</p>
              <p className="text-xs text-muted-foreground">Consider routing 15% of GPT-4 requests to GPT-3.5 for cost savings</p>
            </div>
          </div>
          <div className="flex gap-3 p-3 bg-secondary bg-opacity-50 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-foreground font-medium">API key approaching rate limit</p>
              <p className="text-xs text-muted-foreground">Key prod-api-001 is at 89% of daily quota</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
