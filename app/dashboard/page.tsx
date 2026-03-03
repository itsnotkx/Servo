'use client'

import { useState } from 'react'
import Sidebar from '@/components/sidebar'
import DashboardContent from '@/components/dashboard-content'

export default function Dashboard() {
  const [activePage, setActivePage] = useState('dashboard')

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <DashboardContent page={activePage} />
    </div>
  )
}
