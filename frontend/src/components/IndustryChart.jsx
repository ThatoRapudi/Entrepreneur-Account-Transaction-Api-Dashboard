import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts'
import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import Panel from './Panel'

function buildUrl(days, lifecycleStage) {
  const params = new URLSearchParams({ days: String(days) })
  if (lifecycleStage) params.set('lifecycle_stage', lifecycleStage)
  return `/api/analytics/by-industry?${params.toString()}`
}

export default function IndustryChart({ days, lifecycleStage }) {
  const url = buildUrl(days, lifecycleStage)

  const { data, loading } = useFetch(() => apiGet(url), [url])

  const industries = data?.industries ?? []
  const total = industries.reduce((sum, row) => sum + row.account_count, 0) || 1

  const chartData = industries.map((row) => ({
    industry: row.industry,
    accounts: row.account_count,
    pctLabel: `${Math.round((row.account_count / total) * 100)}%`,
  }))

  return (
    <Panel title="By industry" subtitle={`last ${days} days`}>
      {loading ? (
        <p className="panel-empty">Loading&hellip;</p>
      ) : (
        <div className="panel-chart">
          <ResponsiveContainer>
            <BarChart data={chartData} margin={{ top: 20, right: 8, left: 24, bottom: 40 }}>
              <CartesianGrid vertical={false} stroke="#e1e0d9" />
              <XAxis dataKey="industry" tick={{ fontSize: 11 }} interval={0} angle={-30} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip formatter={(value, _name, entry) => [`${value} accounts (${entry.payload.pctLabel})`, 'Accounts']} />
              <Bar dataKey="accounts" fill="#2a78d6" radius={[4, 4, 0, 0]}>
                <LabelList dataKey="pctLabel" position="top" style={{ fontSize: 11, fill: '#52514e' }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </Panel>
  )
}
