import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import Panel from './Panel'

const STAGE_ORDER = ['brand_new', 'early', 'growing', 'mature', 'aged']
const STAGE_COLORS = {
  brand_new: '#2a78d6',
  early: '#eb6834',
  growing: '#1baf7a',
  mature: '#eda100',
  aged: '#e87ba4',
}

/**
 * Donut of accounts by lifecycle stage. Both the slices and the legend
 * chips are clickable - clicking a stage calls onSelectStage, which App
 * uses to set the AccountsList filter immediately. Clicking the already-
 * selected stage clears the filter (toggle off).
 *
 * Takes the stage-count dict either directly via `byStage`, or (for the
 * original Dashboard usage) pulled from `summary.by_lifecycle_stage` -
 * this lets the Transactions/Loans/Insurance pages reuse the exact same
 * donut against their own by_lifecycle_stage breakdowns, with whatever
 * title/subtitle fits that page, instead of a near-duplicate component.
 */
export default function LifecycleChart({
  summary,
  byStage: byStageProp,
  selectedStage,
  onSelectStage,
  title = 'By lifecycle stage',
  subtitle = 'click a stage to filter',
}) {
  const byStage = byStageProp ?? summary?.by_lifecycle_stage ?? {}
  const total = Object.values(byStage).reduce((sum, n) => sum + n, 0) || 1

  const chartData = STAGE_ORDER
    .filter((stage) => byStage[stage] !== undefined)
    .map((stage) => ({
      name: stage,
      value: byStage[stage],
      pct: Math.round((byStage[stage] / total) * 100),
    }))

  const toggleStage = (stage) => onSelectStage(selectedStage === stage ? '' : stage)

  return (
    <Panel title={title} subtitle={subtitle}>
      {chartData.length === 0 ? (
        <p className="panel-empty">No data for this filter.</p>
      ) : (
        <>
          <div className="panel-chart">
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  onClick={(entry) => toggleStage(entry.name)}
                  cursor="pointer"
                >
                  {chartData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={STAGE_COLORS[entry.name]}
                      stroke={selectedStage === entry.name ? '#1a1a19' : undefined}
                      strokeWidth={selectedStage === entry.name ? 2 : 0}
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name, entry) => [`${value} (${entry.payload.pct}%)`, name]} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="legend-row">
            {chartData.map((entry) => (
              <button
                type="button"
                className={`legend-item ${selectedStage === entry.name ? 'selected' : ''}`}
                key={entry.name}
                onClick={() => toggleStage(entry.name)}
              >
                <span className="legend-swatch" style={{ background: STAGE_COLORS[entry.name] }} />
                <span className="legend-item-name">{entry.name}</span>
                <span>{entry.value} &middot; {entry.pct}%</span>
              </button>
            ))}
          </div>
        </>
      )}
    </Panel>
  )
}
