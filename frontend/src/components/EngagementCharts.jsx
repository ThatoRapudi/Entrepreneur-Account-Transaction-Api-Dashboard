import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import Panel from './Panel'

function buildUrl(endpoint, params, lifecycleStage) {
  const search = new URLSearchParams(params)
  if (lifecycleStage) search.set('lifecycle_stage', lifecycleStage)
  return `${endpoint}?${search.toString()}`
}

/**
 * WAU/MAU had no dashboard-level view at all before this - only a
 * per-account endpoint existed (GET /api/accounts/{id}/wau|mau).
 *
 * WAU here means "of accounts in week N of their own life (1-4), what
 * fraction are active" - an early-adoption curve, not a calendar week.
 * MAU is a real calendar-month trend for established accounts. They're
 * genuinely different axes, which is why they're two charts, not one.
 */
export default function EngagementCharts({ lifecycleStage }) {
  const wauUrl = buildUrl('/api/analytics/wau-summary', {}, lifecycleStage)
  const mauUrl = buildUrl('/api/analytics/mau-summary', { months: 6 }, lifecycleStage)

  const { data: wauData, loading: wauLoading } = useFetch(() => apiGet(wauUrl), [wauUrl])
  const { data: mauData, loading: mauLoading } = useFetch(() => apiGet(mauUrl), [mauUrl])

  const wauChart = (wauData?.weeks ?? []).map((w) => ({ label: `Week ${w.week_number}`, rate: w.active_rate }))
  const mauChart = (mauData?.series ?? []).map((m) => ({ label: m.month, rate: m.active_rate }))

  return (
    <>
      <Panel title="Weekly active users" subtitle="% active by week of account life">
        {wauLoading ? (
          <p className="panel-empty">Loading&hellip;</p>
        ) : wauChart.length === 0 ? (
          <p className="panel-empty">No WAU data for this filter.</p>
        ) : (
          <div className="panel-chart">
            <ResponsiveContainer>
              <BarChart data={wauChart}>
                <CartesianGrid vertical={false} stroke="#e1e0d9" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" width={36} />
                <Tooltip formatter={(v) => [`${v}%`, 'Active']} />
                <Bar dataKey="rate" fill="#01466f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Panel>

      <Panel title="Monthly active users" subtitle="% active, last 6 months">
        {mauLoading ? (
          <p className="panel-empty">Loading&hellip;</p>
        ) : mauChart.length === 0 ? (
          <p className="panel-empty">No MAU data for this filter.</p>
        ) : (
          <div className="panel-chart">
            <ResponsiveContainer>
              <LineChart data={mauChart}>
                <CartesianGrid vertical={false} stroke="#e1e0d9" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} unit="%" width={36} />
                <Tooltip formatter={(v) => [`${v}%`, 'Active']} />
                <Line type="monotone" dataKey="rate" stroke="#e73a34" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Panel>
    </>
  )
}
