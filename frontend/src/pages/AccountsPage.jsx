import { useDashboard } from '../context/DashboardContext'
import EngagementCharts from '../components/EngagementCharts'
import AdoptionFunnel from '../components/AdoptionFunnel'
import DenseListPanel from '../components/DenseListPanel'
import AccountsList from '../components/AccountsList'

/**
 * Everything account-level that used to crowd the bottom of one long
 * page: WAU/MAU engagement, the service adoption funnel, top accounts,
 * churn watchlist, churned accounts, and the full account list/search.
 */
export default function AccountsPage() {
  const { filters } = useDashboard()
  const lifecycleStage = filters.lifecycle_stage

  return (
    <>
      <h1 className="page-title">Accounts</h1>
      <p className="page-subtitle">Engagement, service adoption, and the full account list</p>

      <div className="grid-row">
        <EngagementCharts lifecycleStage={lifecycleStage} />
      </div>

      <div className="grid-row">
        <AdoptionFunnel lifecycleStage={lifecycleStage} />
      </div>

      <div className="grid-row">
        <DenseListPanel
          title="Churn watchlist"
          subtitle="highest risk, still active"
          endpoint="/api/analytics/churn-watchlist"
          limit={5}
          lifecycleStage={lifecycleStage}
          rowsPath="watchlist"
          renderTag={(row) => `${Math.round(row.churn_risk_score)}% risk`}
          tagClassName="dense-row-tag"
          emptyText="No accounts at risk right now."
          collapsible
        />
        <DenseListPanel
          title="Churned accounts"
          subtitle="already inactive"
          endpoint="/api/analytics/churned-accounts"
          limit={5}
          lifecycleStage={lifecycleStage}
          rowsPath="churned_accounts"
          renderTag={(row) => `${row.lifecycle_stage} · ${row.days_since_open}d old`}
          tagClassName="dense-row-tag"
          emptyText="No churned accounts right now."
          collapsible
        />
      </div>

      <div className="grid-row">
        <DenseListPanel
          title="Top accounts"
          subtitle="by POS transaction volume"
          endpoint="/api/analytics/top-accounts"
          limit={5}
          lifecycleStage={lifecycleStage}
          rowsPath="top_accounts"
          renderTag={(row) => `${row.transaction_count} transactions processed`}
          tagTitle="Total POS transactions processed - a proxy for how actively this account uses its POS service"
          emptyText="No accounts yet."
          collapsible
        />
      </div>

      <AccountsList filters={filters} />
    </>
  )
}
