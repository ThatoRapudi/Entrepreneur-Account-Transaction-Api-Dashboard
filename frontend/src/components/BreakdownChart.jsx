import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts'
import Panel from './Panel'

/**
 * One reusable bar chart for "count of X by category" breakdowns -
 * payment method, card type, loan term, insurance type all share this
 * exact shape (a label, a count, a percentage of the total), so one
 * component renders all of them instead of near-duplicate files.
 *
 * data: [{ label, count, extra? }] - extra is an optional pre-formatted
 * string (e.g. a rand total) appended to the tooltip.
 */
export default function BreakdownChart({ title, subtitle, data, color = '#2a78d6', emptyText = 'No data for this filter.' }) {
  const total = data.reduce((sum, row) => sum + row.count, 0) || 1
  const chartData = data.map((row) => ({
    label: row.label,
    count: row.count,
    extra: row.extra,
    pctLabel: `${Math.round((row.count / total) * 100)}%`,
  }))

  return (
    <Panel title={title} subtitle={subtitle}>
      {chartData.length === 0 ? (
        <p className="panel-empty">{emptyText}</p>
      ) : (
        <div className="panel-chart">
          <ResponsiveContainer>
            <BarChart data={chartData} margin={{ top: 20, right: 8, left: 24, bottom: 40 }}>
              <CartesianGrid vertical={false} stroke="#e1e0d9" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} angle={-25} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                formatter={(value, _name, entry) => [
                  `${value} (${entry.payload.pctLabel})${entry.payload.extra ? ' · ' + entry.payload.extra : ''}`,
                  'Count',
                ]}
              />
              <Bar dataKey="count" fill={color} radius={[4, 4, 0, 0]}>
                <LabelList dataKey="pctLabel" position="top" style={{ fontSize: 11, fill: '#52514e' }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </Panel>
  )
}
