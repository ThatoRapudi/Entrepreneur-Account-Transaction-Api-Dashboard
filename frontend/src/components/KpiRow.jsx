/**
 * KPI cards + lifecycle donut both read from /api/analytics/summary.
 * Fetching it once in App and passing it down (rather than each panel
 * polling separately) keeps us well under the 10/min limit on that
 * endpoint while still refreshing both panels together.
 */
export default function KpiRow({ summary }) {
  const totalTx = summary?.total_transactions ?? '-'

  return (
    <div className="kpi-row">
      <div className="metric-card">
        <p className="metric-label">Total accounts</p>
        <p className="metric-value">{summary?.total_accounts ?? '-'}</p>
      </div>
      <div className="metric-card">
        <p className="metric-label">Active accounts</p>
        <p className="metric-value">{summary?.active_accounts ?? '-'}</p>
      </div>
      <div className="metric-card">
        <p className="metric-label">Inactive accounts</p>
        <p className="metric-value">{summary?.inactive_accounts ?? '-'}</p>
      </div>
      <div className="metric-card">
        <p className="metric-label">Total transactions</p>
        <p className="metric-value">{totalTx}</p>
      </div>
    </div>
  )
}
