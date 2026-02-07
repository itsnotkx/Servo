'use client'

import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Bell, Lock, Users, LogOut } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="p-8 max-w-2xl">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground mb-2">Settings</h2>
        <p className="text-muted-foreground">Manage your account settings and preferences</p>
      </div>

      {/* Account Settings */}
      <Card className="bg-card border-border p-6 mb-6">
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Lock className="w-5 h-5" />
          Account Settings
        </h3>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-muted-foreground block mb-2">Email Address</label>
            <p className="text-foreground font-medium">your@startup.com</p>
            <Button variant="outline" size="sm" className="mt-2 text-foreground border-border hover:bg-secondary bg-transparent">
              Change Email
            </Button>
          </div>
          <div className="border-t border-border pt-4">
            <label className="text-sm text-muted-foreground block mb-2">Password</label>
            <p className="text-foreground text-sm mb-2">Last changed 3 months ago</p>
            <Button variant="outline" size="sm" className="text-foreground border-border hover:bg-secondary bg-transparent">
              Change Password
            </Button>
          </div>
        </div>
      </Card>

      {/* Notifications */}
      <Card className="bg-card border-border p-6 mb-6">
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Bell className="w-5 h-5" />
          Notifications
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-foreground font-medium">Cost Alerts</p>
              <p className="text-sm text-muted-foreground">Notify when spending exceeds threshold</p>
            </div>
            <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
          </div>
          <div className="border-t border-border pt-4 flex items-center justify-between">
            <div>
              <p className="text-foreground font-medium">Daily Reports</p>
              <p className="text-sm text-muted-foreground">Receive daily cost summary</p>
            </div>
            <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
          </div>
          <div className="border-t border-border pt-4 flex items-center justify-between">
            <div>
              <p className="text-foreground font-medium">API Key Changes</p>
              <p className="text-sm text-muted-foreground">Notify on key rotation or revocation</p>
            </div>
            <input type="checkbox" defaultChecked className="w-5 h-5 rounded" />
          </div>
        </div>
      </Card>

      {/* Team Members */}
      <Card className="bg-card border-border p-6 mb-6">
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Users className="w-5 h-5" />
          Team Members
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-secondary bg-opacity-50 rounded-lg">
            <div>
              <p className="text-foreground font-medium">you@startup.com</p>
              <p className="text-xs text-accent">Admin</p>
            </div>
            <p className="text-xs text-muted-foreground">Owner</p>
          </div>
          <div className="flex items-center justify-between p-3 bg-secondary bg-opacity-50 rounded-lg">
            <div>
              <p className="text-foreground font-medium">engineer@startup.com</p>
              <p className="text-xs text-primary">Member</p>
            </div>
            <Button variant="ghost" size="sm" className="text-destructive hover:bg-secondary">
              Remove
            </Button>
          </div>
        </div>
        <Button variant="outline" className="w-full mt-4 text-foreground border-border hover:bg-secondary bg-transparent">
          Invite Team Member
        </Button>
      </Card>

      {/* Danger Zone */}
      <Card className="bg-card border-border border-destructive border-opacity-50 p-6">
        <h3 className="text-lg font-semibold text-destructive mb-4">Danger Zone</h3>
        <div className="space-y-3">
          <div>
            <p className="text-foreground font-medium">Delete Account</p>
            <p className="text-sm text-muted-foreground mb-3">Permanently delete your account and all associated data</p>
            <Button variant="outline" className="text-destructive border-destructive hover:bg-destructive hover:bg-opacity-10 bg-transparent">
              Delete Account
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
