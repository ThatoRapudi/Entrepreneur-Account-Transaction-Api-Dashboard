import { useDashboard } from '../context/DashboardContext'
import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import BreakdownChart from '../components/BreakdownChart'
import LifecycleChart from '../components/LifecycleChart'
import RecordsList from '../components/RecordsList'

const TERM_LABELS = {
  short_term: 'Short-term (1-6mo)',
  medium_term: 'Medium-term (7-24mo)',
  long_term: 'Long-term (25-60mo)',
}

export default function LoansPage() {
  const { filters, handleSelectStage } = useDashboard()
  const lifecycleStage = filters.lifecycle_stage

  const url = lifecycleStage
    ? `/api/analytics/loan-breakdown?lifecycle_stage=${lifecycleStage}`
    : '/api/analytics/loan-breakdown'
  const { data, loading } = useFetch(() => apiGet(url), [url])

  const byTerm = (data?.by_term ?? []).map((row) => ({
    label: TERM_LABELS[row.loan_term] ?? row.loan_term,
    count: row.count,
    extra: `avg R${Math.round(row.avg_amount).toLocaleString('en-ZA')} · total R${Math.round(row.total_amount).toLocaleString('en-ZA')}`,
  }))
  const byIndustry = (data?.by_industry ?? []).map((row) => ({
    label: row.industry,
    count: row.count,
    extra: `R${Math.round(row.total_amount).toLocaleString('en-ZA')} total`,
  }))

  return (
    <>
      <h1 className="page-title">Loans</h1>
      <p className="page-subtitle">Term, amount, and which lifecycle stage takes up credit</p>

      <div className="grid-row">
        <LifecycleChart
          byStage={data?.by_lifecycle_stage}
          selectedStage={lifecycleStage}
          onSelectStage={handleSelectStage}
          title="Loans by lifecycle stage"
          subtitle="click a stage to filter"
        />
        {!loading && (
          <BreakdownChart title="By industry" subtitle="which sectors take up credit" data={byIndustry} color="#01466f" />
        )}
      </div>

      <div className="grid-row">
        {!loading && (
          <BreakdownChart title="By term" subtitle="short, medium, long - capped at R500,000" data={byTerm} color="#e73a34" />
        )}
      </div>

      <RecordsList
        title="Loans"
        endpoint="/api/loans"
        lifecycleStage={lifecycleStage}
        renderMain={(row) => `R${Math.round(row.amount).toLocaleString('en-ZA')} · ${TERM_LABELS[row.loan_term] ?? row.loan_term}`}
        renderTag={(row) => `${row.status}${row.term_months ? ' · ' + row.term_months + 'mo' : ''}`}
        csvFilename="loans.csv"
        csvRow={(row) => ({
          account_id: row.account_id,
          amount: row.amount,
          loan_term: row.loan_term,
          term_months: row.term_months,
          status: row.status,
          application_date: row.application_date,
        })}
      />
    </>
  )
}
