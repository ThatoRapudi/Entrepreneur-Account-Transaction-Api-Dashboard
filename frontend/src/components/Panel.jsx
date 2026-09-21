/**
 * Shared collapsible panel for every chart on the dashboard - a
 * <details>/<summary> so each graph can be opened and closed
 * independently (reuses the exact chevron/collapse CSS already built
 * for the record lists: AccountsList, DenseListPanel, RecordsList),
 * instead of a graph being permanently fixed in its slot on the page.
 *
 * Also fixes the "big empty gap" issue: .panel-body (see styles.css)
 * is a flex child with flex:1, so when this panel sits next to a
 * taller sibling in the same grid row (e.g. the lifecycle donut, which
 * is tall because of its legend chips), the CSS grid stretches this
 * panel to match that height, and the chart inside grows to fill it
 * instead of leaving dead space below a fixed-size chart.
 */
export default function Panel({ title, subtitle, defaultOpen = true, children, className = '' }) {
  return (
    <details className={`panel ${className}`.trim()} open={defaultOpen}>
      <summary className="panel-header">
        <span className="panel-title">{title}</span>
        <span className="panel-subtitle">{subtitle}</span>
      </summary>
      <div className="panel-body">{children}</div>
    </details>
  )
}
