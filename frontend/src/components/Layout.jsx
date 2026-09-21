import { Outlet } from 'react-router-dom'
import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import { useDashboard } from '../context/DashboardContext'
import Sidebar from './Sidebar'
import Toolbar from './Toolbar'
import KpiRow from './KpiRow'

/**
 * Persistent shell around every protected page: sidebar nav on the
 * left; KPI strip and filter toolbar always visible at the top so
 * filters carry over between Dashboard and Accounts instead of
 * resetting per page.
 *
 * /api/analytics/summary is fetched once here (not per-page) and
 * handed to whichever page needs it via route outlet context - keeps
 * every page under the same rate limit budget on that endpoint. This
 * is mock data with no live updates, so it fetches once and again
 * whenever a filter/day-range changes - no background polling.
 */
export default function Layout() {
  const { filters, setFilters, days, setDays } = useDashboard()

  const { data: summary } = useFetch(() => apiGet(`/api/analytics/summary?days=${days}`), [days])

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <Toolbar filters={filters} onFilterChange={setFilters} days={days} onDaysChange={setDays} />
        <KpiRow summary={summary} />

        <div className="page-content">
          <Outlet context={{ summary }} />
        </div>
      </div>
    </div>
  )
}
