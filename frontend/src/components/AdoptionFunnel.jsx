import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import Panel from './Panel'

/**
 * Service adoption funnel: onboarded -> activated (first POS use) ->
 * insurance -> loans, with drop-off and churn shown at each step
 * instead of a static product-count snapshot. See the /adoption-funnel
 * endpoint's docstring for exactly what each number means.
 */
export default function AdoptionFunnel({ lifecycleStage }) {
  const url = lifecycleStage
    ? `/api/analytics/adoption-funnel?lifecycle_stage=${lifecycleStage}`
    : '/api/analytics/adoption-funnel'

  const { data, loading } = useFetch(() => apiGet(url), [url])

  const stages = data?.funnel ?? []
  const base = stages[0]?.reached_count || 1

  return (
    <Panel title="Service adoption funnel" subtitle="onboarded → activated → cross-sold">
      <p className="funnel-explainer">
        How far accounts get after opening: onboarded, then using POS, then adding
        insurance, then a loan. The drop-off below each stage is how many accounts
        never moved on to it - and how many of those have since churned.
      </p>

      {loading ? (
        <p className="panel-empty">Loading&hellip;</p>
      ) : stages.length === 0 ? (
        <p className="panel-empty">No accounts match this filter.</p>
      ) : (
        <div className="funnel-row">
          {stages.map((stage, i) => {
            const pct = Math.round((stage.reached_count / base) * 100)
            return (
              <div className="funnel-stage-block" key={stage.stage}>
                <div className="funnel-stage">
                  <span className="funnel-stage-label">{stage.stage}</span>
                  <div className="funnel-bar-track">
                    <div className="funnel-bar-fill" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="funnel-stage-value">{stage.reached_count} &middot; {pct}%</span>
                </div>
                {i > 0 && stage.dropped_count > 0 && (
                  <p className="funnel-dropoff">
                    &minus; {stage.dropped_count} didn&rsquo;t reach this stage
                    {stage.churned_count > 0 ? ` (${stage.churned_count} since churned)` : ''}
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}
    </Panel>
  )
}
