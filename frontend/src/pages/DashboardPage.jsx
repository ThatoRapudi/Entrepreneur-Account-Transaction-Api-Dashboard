import { useOutletContext } from 'react-router-dom'
import { useDashboard } from '../context/DashboardContext'
import TrendChart from '../components/TrendChart'
import LifecycleChart from '../components/LifecycleChart'
import IndustryChart from '../components/IndustryChart'
import ActivitySummary from '../components/ActivitySummary'

/**
 * The trimmed landing view - new accounts opened, transaction volume,
 * by lifecycle stage, by industry, plus a recent-activity summary.
 * Everything else (WAU/MAU, funnel, watchlist, account list) lives on
 * the Accounts page so this stays a quick read.
 *
 * The four charts share one "Last N days" rolling window (set in the
 * toolbar) - a separate control from the Accounts page's specific
 * opened-after/opened-before date search.
 */
export default function DashboardPage() {
  const { summary } = useOutletContext()
  const { days, filters, handleSelectStage } = useDashboard()
  const lifecycleStage = filters.lifecycle_stage

  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-subtitle">
        Tracking new account growth and transaction activity across entrepreneurial accounts
      </p>

      <div className="grid-row">
        <LifecycleChart
          summary={summary}
          selectedStage={lifecycleStage}
          onSelectStage={handleSelectStage}
        />
        <IndustryChart days={days} lifecycleStage={lifecycleStage} />
      </div>

      <div className="grid-row">
        <TrendChart
          title="New accounts opened"
          endpoint="/api/analytics/accounts-timeseries"
          color="#01466f"
          days={days}
          lifecycleStage={lifecycleStage}
        />
        <TrendChart
          title="Transaction volume"
          endpoint="/api/analytics/transactions-timeseries"
          color="#e73a34"
          days={days}
          lifecycleStage={lifecycleStage}
          showValue
        />
      </div>

      <div className="grid-row">
        <ActivitySummary days={days} lifecycleStage={lifecycleStage} />
      </div>
    </>
  )
}
