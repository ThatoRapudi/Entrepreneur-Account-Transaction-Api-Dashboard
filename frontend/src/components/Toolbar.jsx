const LIFECYCLE_STAGES = ['brand_new', 'early', 'growing', 'mature', 'aged']
const DATE_RANGES = [30, 60, 90]

/**
 * Filter controls (lifecycle stage, status, opened-date search) plus the
 * trend-chart day-range picker. These were two separate files, but they
 * always render together in one toolbar row, so they're merged into one.
 *
 * filters.lifecycle_stage flows into every other panel on the dashboard
 * (App passes it down) - this is the one control that drives all of them.
 *
 * The opened-after/opened-before date inputs are a precise search on
 * the Accounts list only (find accounts opened in a specific calendar
 * window) - they don't move the trend/industry/lifecycle charts. The
 * "Last N days" dropdown is the separate, rolling-window control for
 * those. Titles below spell this out since both are date pickers.
 */
export default function Toolbar({ filters, onFilterChange, days, onDaysChange }) {
  const updateFilter = (key, value) => onFilterChange({ ...filters, [key]: value })

  return (
    <div className="toolbar">
      <div className="filter-bar">
        <select value={filters.lifecycle_stage} onChange={(e) => updateFilter('lifecycle_stage', e.target.value)}>
          <option value="">Lifecycle stage: all</option>
          {LIFECYCLE_STAGES.map((stage) => (
            <option key={stage} value={stage}>{stage}</option>
          ))}
        </select>

        <select value={filters.status_filter} onChange={(e) => updateFilter('status_filter', e.target.value)}>
          <option value="">Status: all</option>
          <option value="active">active</option>
          <option value="inactive">inactive</option>
        </select>

        <input
          type="date"
          aria-label="Opened after"
          title="Search accounts opened on or after this date - affects the accounts list only"
          value={filters.opened_after}
          onChange={(e) => updateFilter('opened_after', e.target.value)}
        />
        <input
          type="date"
          aria-label="Opened before"
          title="Search accounts opened on or before this date - affects the accounts list only"
          value={filters.opened_before}
          onChange={(e) => updateFilter('opened_before', e.target.value)}
        />
      </div>

      <select
        className="date-range-select"
        value={days}
        onChange={(e) => onDaysChange(Number(e.target.value))}
        aria-label="Date range"
        title="Rolling window for the trend, industry, and lifecycle charts"
      >
        {DATE_RANGES.map((n) => (
          <option key={n} value={n}>Last {n} days</option>
        ))}
      </select>
    </div>
  )
}
