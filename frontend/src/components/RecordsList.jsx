import { useEffect, useState } from 'react'
import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import { downloadCsv } from '../utils/csvExport'

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100]

/**
 * Generic paginated/exportable record list for the Transactions, Loans,
 * and Insurance pages - the same collapsible-panel/rows-per-page/CSV-
 * export shape as AccountsList, just parameterized by endpoint and a
 * row renderer instead of re-writing that shape three more times.
 *
 * endpoint: base API path (e.g. "/api/transactions")
 * lifecycleStage: optional - added to the query, same convention as
 *   every other panel, so this list moves with the global filter too.
 * renderMain / renderTag: (row) => string, for the two-line row layout.
 * csvRow: (row) => object, the flat row written to the exported CSV.
 */
export default function RecordsList({ title, endpoint, lifecycleStage, renderMain, renderTag, csvRow, csvFilename }) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  useEffect(() => {
    setPage(1)
  }, [lifecycleStage, pageSize])

  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (lifecycleStage) params.set('lifecycle_stage', lifecycleStage)
  const query = params.toString()

  const { data, loading } = useFetch(() => apiGet(`${endpoint}?${query}`), [endpoint, query])

  const rows = data ?? []
  const hasNextPage = rows.length === pageSize

  const handleExport = () => downloadCsv(csvFilename, rows.map(csvRow))

  return (
    <details className="panel" open>
      <summary className="panel-header">
        <span className="panel-title">{title} ({rows.length}{hasNextPage ? '+' : ''})</span>
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
          <p className="panel-empty">No records match this filter.</p>
        ) : (
          rows.map((row) => (
            <div className="dense-row" key={row.id}>
              <span className="dense-row-main">{renderMain(row)}</span>
              <span className="dense-row-tag">{renderTag(row)}</span>
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
