import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import Panel from './Panel'

function shortDate(iso) {
  const d = new Date(iso)
  // Uppercased because this is an axis label (structural), not data content.
  return d.toLocaleDateString('en-ZA', { day: '2-digit', month: 'short' }).toUpperCase()
}

function buildUrl(endpoint, days, lifecycleStage) {
  const params = new URLSearchParams({ days: String(days) })
  if (lifecycleStage) params.set('lifecycle_stage', lifecycleStage)
  return `${endpoint}?${params.toString()}`
}

/**
 * Shared line-chart panel for the two growth trends (new accounts opened,
 * transaction volume) - they only ever differed in endpoint/color/title,
 * so one component renders both instead of two near-duplicate files.
 *
 * lifecycleStage: when set, scopes the series to that stage so this panel
 * moves together with the lifecycle donut/filter instead of always
 * showing everyone.
 *
 * showValue: when true, also totals a `total_amount` field from the
 * series and shows it in the subtitle - used for transaction volume,
 * where the rand value matters as much as the count.
 */
export default function TrendChart({ title, endpoint, color, days, lifecycleStage, showValue }) {
  const url = buildUrl(endpoint, days, lifecycleStage)
  const { data, loading } = useFetch(() => apiGet(url), [url])

  const series = data?.series ?? []
  const chartData = series.map((point) => ({ date: shortDate(point.date), count: point.count }))

  const totalValue = showValue
    ? series.reduce((sum, point) => sum + (point.total_amount || 0), 0)
    : null

  const subtitle = (
    <>
      last {days} days
      {totalValue !== null && ` · R${Math.round(totalValue).toLocaleString('en-ZA')} total`}
    </>
  )

  return (
    <Panel title={title} subtitle={subtitle}>
      {loading ? (
        <p className="panel-empty">Loading&hellip;</p>
      ) : (
        <div className="panel-chart">
          <ResponsiveContainer>
            <LineChart data={chartData}>
              <CartesianGrid vertical={false} stroke="#e1e0d9" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={Math.ceil(chartData.length / 8)} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} width={28} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke={color} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Panel>
  )
}
