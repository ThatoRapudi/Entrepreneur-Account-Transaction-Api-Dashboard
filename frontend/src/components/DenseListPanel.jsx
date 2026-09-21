import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'

function buildUrl(endpoint, limit, lifecycleStage) {
  const params = new URLSearchParams({ limit: String(limit) })
  if (lifecycleStage) params.set('lifecycle_stage', lifecycleStage)
  return `${endpoint}?${params.toString()}`
}

/**
 * Shared "ranked business list" panel. Top accounts and the churn
 * watchlist are the same shape - a business name plus one tag per row -
 * so one component renders both instead of two near-duplicate files.
 *
 * lifecycleStage: when set, scopes the list to that stage so this panel
 * moves together with the lifecycle donut/filter.
 *
 * collapsible: renders as a native <details>/<summary> so the panel can
 * be tucked away without custom expand/collapse state or CSS. Defaults
 * open (defaultOpen=true) so the data is visible right away - the
 * summary still shows a chevron and toggles closed on click, but
 * starting collapsed with no visual cue previously read as "broken/
 * empty" rather than "click to expand".
 */
export default function DenseListPanel({
  title,
  subtitle,
  endpoint,
  limit = 5,
  lifecycleStage,
  rowsPath,
  renderTag,
  tagClassName = 'dense-row-meta',
  tagTitle,
  emptyText,
  collapsible,
  defaultOpen = true,
}) {
  const url = buildUrl(endpoint, limit, lifecycleStage)
  const { data, loading } = useFetch(() => apiGet(url), [url])

  const rows = data?.[rowsPath] ?? []

  const list = (
    <div className="dense-list">
      {loading ? (
        <p className="panel-empty">Loading&hellip;</p>
      ) : rows.length === 0 ? (
        <p className="panel-empty">{emptyText}</p>
      ) : (
        rows.map((row) => (
          <div className="dense-row" key={row.account_id}>
            <span className="dense-row-main">{row.business_name}</span>
            <span className={tagClassName} title={tagTitle}>{renderTag(row)}</span>
          </div>
        ))
      )}
    </div>
  )

  const header = (
    <>
      <span className="panel-title">{title}</span>
      <span className="panel-subtitle">{subtitle}</span>
    </>
  )

  if (collapsible) {
    return (
      <details className="panel" open={defaultOpen}>
        <summary className="panel-header">{header}</summary>
        {list}
      </details>
    )
  }

  return (
    <div className="panel">
      <div className="panel-header">{header}</div>
      {list}
    </div>
  )
}
