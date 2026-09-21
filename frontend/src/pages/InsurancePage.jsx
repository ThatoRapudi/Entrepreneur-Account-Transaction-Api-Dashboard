import { useDashboard } from '../context/DashboardContext'
import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import BreakdownChart from '../components/BreakdownChart'
import LifecycleChart from '../components/LifecycleChart'
import RecordsList from '../components/RecordsList'
import DenseListPanel from '../components/DenseListPanel'

export default function InsurancePage() {
  const { filters, handleSelectStage } = useDashboard()
  const lifecycleStage = filters.lifecycle_stage

  const url = lifecycleStage
    ? `/api/analytics/insurance-breakdown?lifecycle_stage=${lifecycleStage}`
    : '/api/analytics/insurance-breakdown'
  const { data, loading } = useFetch(() => apiGet(url), [url])

  const byType = (data?.by_type ?? []).map((row) => ({ label: row.policy_type, count: row.count }))
  const byIndustry = (data?.by_industry ?? []).map((row) => ({ label: row.industry, count: row.count }))

  return (
    <>
      <h1 className="page-title">Insurance</h1>
      <p className="page-subtitle">What's covered, and which lifecycle stage takes up cover</p>

      <div className="grid-row">
        <LifecycleChart
          byStage={data?.by_lifecycle_stage}
          selectedStage={lifecycleStage}
          onSelectStage={handleSelectStage}
          title="Policies by lifecycle stage"
          subtitle="click a stage to filter"
        />
        {!loading && (
          <BreakdownChart title="By industry" subtitle="which sectors take up cover" data={byIndustry} color="#e87ba4" />
        )}
      </div>

      <div className="grid-row">
        {!loading && (
          <BreakdownChart title="By policy type" subtitle="property, stock, liability, equipment, vehicle" data={byType} color="#1baf7a" />
        )}
        <DenseListPanel
          title="Top accounts"
          subtitle="by policies held"
          endpoint="/api/analytics/top-accounts-insurance"
          limit={5}
          lifecycleStage={lifecycleStage}
          rowsPath="top_accounts"
          renderTag={(row) => `${row.policy_count} policies · ${row.policy_breakdown}`}
          tagTitle="Total policies held and the breakdown by type - do they cover everything, or just one thing?"
          emptyText="No accounts with policies yet."
          collapsible
        />
      </div>

      <RecordsList
        title="Insurance policies"
        endpoint="/api/policies/insurance"
        lifecycleStage={lifecycleStage}
        renderMain={(row) => row.policy_type}
        renderTag={(row) => row.status}
        csvFilename="insurance_policies.csv"
        csvRow={(row) => ({
          account_id: row.account_id,
          policy_type: row.policy_type,
          status: row.status,
          application_date: row.application_date,
        })}
      />
    </>
  )
}
