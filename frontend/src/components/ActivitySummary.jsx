import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import Panel from './Panel'

/**
 * Replaces the old second-by-second "4s ago / 21s ago" feed with grouped
 * counts over a period - per feedback, precise timestamps weren't the
 * point for a monitoring dashboard; what happened in this window is.
 */
export default function ActivitySummary({ days, lifecycleStage }) {
  const url = lifecycleStage
    ? `/api/analytics/activity-summary?days=${days}&lifecycle_stage=${lifecycleStage}`
    : `/api/analytics/activity-summary?days=${days}`

  const { data, loading } = useFetch(() => apiGet(url), [url])

  return (
    <Panel title="Recent activity" subtitle={`last ${days} days`}>
      {loading ? (
        <p className="panel-empty">Loading&hellip;</p>
      ) : (
        <div className="activity-summary-grid">
          <div className="activity-stat">
            <p className="activity-stat-label">New accounts opened</p>
            <p className="activity-stat-value">{data?.new_accounts ?? 0}</p>
          </div>
          <div className="activity-stat">
            <p className="activity-stat-label">POS payments</p>
            <p className="activity-stat-value">{data?.pos_payments ?? 0}</p>
          </div>
          <div className="activity-stat">
            <p className="activity-stat-label">Loans applied</p>
            <p className="activity-stat-value">{data?.loans_applied ?? 0}</p>
          </div>
          <div className="activity-stat">
            <p className="activity-stat-label">Insurance activated</p>
            <p className="activity-stat-value">{data?.insurance_activated ?? 0}</p>
          </div>
          <div className="activity-stat">
            <p className="activity-stat-label">Deposits &amp; EFTs received</p>
            <p className="activity-stat-value">{data?.other_income ?? 0}</p>
          </div>
          <div className="activity-stat">
            <p className="activity-stat-label" title="Currently inactive accounts - a snapshot, not limited to this window">
              Churned accounts
            </p>
            <p className="activity-stat-value">{data?.churned_accounts ?? 0}</p>
          </div>
        </div>
      )}
    </Panel>
  )
}
