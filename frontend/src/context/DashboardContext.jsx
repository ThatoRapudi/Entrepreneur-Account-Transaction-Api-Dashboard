import { createContext, useContext, useState } from 'react'

const DashboardContext = createContext(null)

/**
 * Filters and the day-range are shared across every page (Dashboard,
 * Accounts) plus the persistent Toolbar in Layout - lifted here instead
 * of prop-drilled through routes, so selecting a lifecycle stage or a
 * day range on one page still applies when you navigate to the other.
 */
export function DashboardProvider({ children }) {
  const [filters, setFilters] = useState({
    lifecycle_stage: '',
    status_filter: '',
    opened_after: '',
    opened_before: '',
  })

  const [days, setDays] = useState(30)

  // Clicking a lifecycle donut slice/legend sets this filter directly.
  const handleSelectStage = (stage) => {
    setFilters((f) => ({ ...f, lifecycle_stage: stage }))
  }

  return (
    <DashboardContext.Provider
      value={{ filters, setFilters, days, setDays, handleSelectStage }}
    >
      {children}
    </DashboardContext.Provider>
  )
}

export function useDashboard() {
  const ctx = useContext(DashboardContext)
  if (!ctx) throw new Error('useDashboard must be used within a DashboardProvider')
  return ctx
}
