'use client'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts'
import { Download, CreditCard } from 'lucide-react'

const monthlyData = [
  { month: 'Oct', cost: 1800, limit: 3000 },
  { month: 'Nov', cost: 2100, limit: 3000 },
  { month: 'Dec', cost: 2340, limit: 3500 },
  { month: 'Jan', cost: 2150, limit: 3500 },
]

const invoiceData = [
  {
    id: 'INV-2025-001',
    date: 'Jan 1, 2025',
    amount: 2340,
    status: 'paid',
    dueDate: 'Jan 31, 2025',
  },
  {
    id: 'INV-2024-012',
    date: 'Dec 1, 2024',
    amount: 2100,
    status: 'paid',
    dueDate: 'Dec 31, 2024',
  },
  {
    id: 'INV-2024-011',
    date: 'Nov 1, 2024',
    amount: 1900,
    status: 'paid',
    dueDate: 'Nov 30, 2024',
  },
]

export default function BillingPage() {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground mb-2">Billing</h2>
        <p className="text-muted-foreground">Manage your subscription, invoices, and payment methods</p>
      </div>

      {/* Billing Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card className="bg-card border-border p-6">
          <p className="text-muted-foreground text-sm mb-1">Current Plan</p>
          <p className="text-2xl font-bold text-foreground">Growth</p>
          <p className="text-xs text-accent mt-2">$3,500/month</p>
        </Card>

        <Card className="bg-card border-border p-6">
          <p className="text-muted-foreground text-sm mb-1">Billing Cycle</p>
          <p className="text-2xl font-bold text-foreground">Jan 1-31</p>
          <p className="text-xs text-muted-foreground mt-2">Next renewal: Feb 1</p>
        </Card>

        <Card className="bg-card border-border p-6">
          <p className="text-muted-foreground text-sm mb-1">Current Usage</p>
          <p className="text-2xl font-bold text-foreground">$2,340</p>
          <div className="mt-3 w-full h-2 bg-secondary rounded-full overflow-hidden">
            <div className="h-full w-2/3 bg-gradient-to-r from-primary to-accent" />
          </div>
          <p className="text-xs text-muted-foreground mt-1">66.9% of limit</p>
        </Card>

        <Card className="bg-card border-border p-6">
          <p className="text-muted-foreground text-sm mb-1">Next Payment</p>
          <p className="text-2xl font-bold text-foreground">Feb 1, 2025</p>
          <p className="text-xs text-muted-foreground mt-2">~$2,500 estimated</p>
        </Card>
      </div>

      {/* Cost Trend Chart */}
      <Card className="bg-card border-border p-6 mb-8">
        <h3 className="text-lg font-semibold text-foreground mb-4">Monthly Spending & Limits</h3>
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
            <Legend />
            <Bar dataKey="cost" fill="#3b82f6" name="Actual Cost" radius={[8, 8, 0, 0]} />
            <Bar dataKey="limit" fill="#2d3748" name="Monthly Limit" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Payment Method */}
        <Card className="bg-card border-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">Payment Method</h3>
            <CreditCard className="w-5 h-5 text-primary" />
          </div>
          <div className="bg-gradient-to-br from-primary to-accent rounded-lg p-6 text-white mb-4 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-white opacity-10 rounded-full -mr-8 -mt-8" />
            <p className="text-sm mb-2">Visa Ending in</p>
            <p className="text-2xl font-bold tracking-widest">•••• 4242</p>
            <p className="text-xs mt-4">Expires 12/28</p>
          </div>
          <Button variant="outline" className="w-full text-foreground border-border hover:bg-secondary bg-transparent">
            Update Payment Method
          </Button>
        </Card>

        {/* Invoices */}
        <div className="lg:col-span-2">
          <Card className="bg-card border-border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">Recent Invoices</h3>
              <Button variant="ghost" size="sm" className="text-primary hover:bg-secondary">
                <Download className="w-4 h-4 mr-1" />
                Download All
              </Button>
            </div>

            <div className="space-y-3">
              {invoiceData.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between p-3 bg-secondary bg-opacity-50 rounded-lg hover:bg-opacity-70 transition">
                  <div className="flex-1">
                    <p className="font-medium text-foreground">{invoice.id}</p>
                    <p className="text-xs text-muted-foreground">{invoice.date}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-foreground">${invoice.amount.toLocaleString()}</p>
                    <p
                      className={`text-xs font-medium ${
                        invoice.status === 'paid' ? 'text-accent' : 'text-primary'
                      }`}
                    >
                      {invoice.status === 'paid' ? '✓ Paid' : 'Pending'}
                    </p>
                  </div>
                  <Button variant="ghost" size="sm" className="ml-4 text-muted-foreground hover:text-foreground">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Billing Info */}
      <Card className="bg-card border-border p-6 mt-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Billing Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="text-sm text-muted-foreground block mb-2">Company Name</label>
            <p className="text-foreground">Acme AI Startup</p>
          </div>
          <div>
            <label className="text-sm text-muted-foreground block mb-2">Email Address</label>
            <p className="text-foreground">billing@acmeai.com</p>
          </div>
          <div>
            <label className="text-sm text-muted-foreground block mb-2">Address</label>
            <p className="text-foreground">123 Tech Street, San Francisco, CA 94105</p>
          </div>
          <div>
            <label className="text-sm text-muted-foreground block mb-2">Tax ID</label>
            <p className="text-foreground">98-1234567</p>
          </div>
        </div>
        <Button variant="outline" className="mt-4 text-foreground border-border hover:bg-secondary bg-transparent">
          Edit Billing Information
        </Button>
      </Card>
    </div>
  )
}
