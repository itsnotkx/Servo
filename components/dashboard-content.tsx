import DashboardOverview from './dashboard-overview'
import ApiKeysPage from './api-keys-page'
import ExecutionLogsPage from './execution-logs-page'
import BillingPage from './billing-page'
import RoutingPage from './routing-page'
import SettingsPage from './settings-page'

interface DashboardContentProps {
  page: string
}

export default function DashboardContent({ page }: DashboardContentProps) {
  return (
    <div className="flex-1 overflow-auto bg-background">
      {page === 'dashboard' && <DashboardOverview />}
      {page === 'api-keys' && <ApiKeysPage />}
      {page === 'logs' && <ExecutionLogsPage />}
      {page === 'routing' && <RoutingPage />}
      {page === 'billing' && <BillingPage />}
      {page === 'settings' && <SettingsPage />}
    </div>
  )
}
