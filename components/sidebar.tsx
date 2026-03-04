'use client';

import { BarChart3, CreditCard, Key, Route, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useUser, useClerk } from '@clerk/nextjs'

interface SidebarProps {
  activePage: string
  setActivePage: (page: string) => void
}

export default function Sidebar({ activePage, setActivePage }: SidebarProps) {
  const { user } = useUser()
  const { signOut } = useClerk()

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'routing', label: 'Routing', icon: Route },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]

  const email = user?.emailAddresses[0]?.emailAddress ?? ''

  return (
    <div className="w-64 border-r border-border bg-sidebar flex flex-col">
      {/* Logo Section */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
            <span className="text-accent-foreground font-bold text-sm">S</span>
          </div>
          <h1 className="text-xl font-bold text-sidebar-foreground">Servo</h1>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-4">
        <div className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = activePage === item.id
            return (
              <Button
                key={item.id}
                variant={isActive ? 'default' : 'ghost'}
                className={`w-full justify-start gap-3 text-base ${
                  isActive
                    ? 'bg-sidebar-primary text-sidebar-primary-foreground'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent'
                }`}
                onClick={() => setActivePage(item.id)}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Button>
            )
          })}
        </div>
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-sidebar-border">
        <div className="bg-sidebar-accent bg-opacity-20 rounded-lg p-3 mb-4">
          <p className="text-xs text-sidebar-accent-foreground font-semibold mb-1">ACCOUNT</p>
          <p className="text-sm text-sidebar-foreground truncate">{email}</p>
        </div>
        <Button
          variant="outline"
          className="w-full text-sidebar-foreground border-sidebar-border hover:bg-sidebar-accent bg-transparent"
          onClick={() => signOut({ redirectUrl: '/' })}
        >
          Sign Out
        </Button>
      </div>
    </div>
  )
}
