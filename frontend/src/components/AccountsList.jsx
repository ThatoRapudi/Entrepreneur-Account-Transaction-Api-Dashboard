import { useEffect, useState } from 'react'
import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import { downloadCsv } from '../utils/csvExport'

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100]

function buildQuery(filters, page, pageSize) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (filters.lifecycle_stage) params.set('lifecycle_stage', filters.lifecycle_stage)
  if (filters.status_filter) params.set('status_filter', filters.status_filter)
  if (filters.opened_after) params.set('opened_after', filters.opened_after)
  if (filters.opened_before) params.set('opened_before', filters.opened_before)
  return params.toString()
}

/**
 * Filtered account search results, driven by the toolbar's filter state
 * and the lifecycle donut's click-to-filter. A native <details>/
 * <summary> (no extra state needed) so it can be tucked away as the
 * account base grows - open by default so the data is visible right
 * away rather than looking empty until someone notices it's clickable.
 */
export default function AccountsList({ filters }) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // A changed filter can make the current page meaningless - jump back
  // to page 1 rather than showing a confusing, possibly-empty page 4.
  useEffect(() => {
    setPage(1)
  }, [filters.lifecycle_stage, filters.status_filter, filters.opened_after, filters.opened_before, pageSize])

  const query = buildQuery(filters, page, pageSize)

  const { data, loading } = useFetch(
    () => apiGet(`/api/accounts?${query}`),
    [query]
  )

  const rows = data ?? []
  const hasNextPage = rows.length === pageSize

  const handleExport = () => {
    downloadCsv(
      'accounts.csv',
      rows.map((r) => ({
        account_id: r.account_id,
        business_name: r.business_name,
        industry: r.industry,
        lifecycle_stage: r.lifecycle_stage,
        status: r.status,
        opening_date: r.opening_date,
        churn_risk_score: r.churn_risk_score,
      }))
    )
  }

  return (
    <details className="panel" open>
      <summary className="panel-header">
        <span className="panel-title">Accounts ({rows.length}{hasNextPage ? '+' : ''})</span>
        <span className="panel-subtitle">click to collapse</span>
      </summary>

      <div className="accounts-toolbar">
        <label className="accounts-toolbar-label">
          Rows per page
          <select value={pageSize} onChange={(e) => setPageSize(Number(e.target.value))}>
            {PAGE_SIZE_OPTIONS.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>
        <button type="button" onClick={handleExport} disabled={rows.length === 0}>
          Export CSV
        </button>
      </div>

      <div className="dense-list">
        {loading ? (
          <p className="panel-empty">Loading&hellip;</p>
        ) : rows.length === 0 ? (
          <p className="panel-empty">No accounts match these filters.</p>
        ) : (
          rows.map((row) => (
            <div className="dense-row" key={row.account_id}>
              <span className="dense-row-main">{row.business_name}</span>
              <span className="dense-row-tag">{row.lifecycle_stage} &middot; {row.status}</span>
            </div>
          ))
        )}
      </div>

      <div className="pagination-row">
        <button type="button" onClick={() => setPage((p) => p - 1)} disabled={page === 1}>
          Prev
        </button>
        <span className="pagination-page">Page {page}</span>
        <button type="button" onClick={() => setPage((p) => p + 1)} disabled={!hasNextPage}>
          Next
        </button>
      </div>
    </details>
  )
}
