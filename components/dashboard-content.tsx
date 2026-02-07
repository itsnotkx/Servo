import DashboardOverview from './pages/dashboard-overview'
import ApiKeysPage from './pages/api-keys-page'
import BillingPage from './pages/billing-page'
import SettingsPage from './pages/settings-page'

interface DashboardContentProps {
  page: string
}

export default function DashboardContent({ page }: DashboardContentProps) {
  return (
    <div className="flex-1 overflow-auto bg-background">
      {page === 'dashboard' && <DashboardOverview />}
      {page === 'api-keys' && <ApiKeysPage />}
      {page === 'billing' && <BillingPage />}
      {page === 'settings' && <SettingsPage />}
    </div>
  )
}
