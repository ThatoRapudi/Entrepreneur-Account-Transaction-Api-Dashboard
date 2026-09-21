import { useDashboard } from '../context/DashboardContext'
import { useFetch } from '../hooks/useFetch'
import { apiGet } from '../api/client'
import BreakdownChart from '../components/BreakdownChart'
import LifecycleChart from '../components/LifecycleChart'
import RecordsList from '../components/RecordsList'
import DenseListPanel from '../components/DenseListPanel'

const PAYMENT_METHOD_LABELS = {
  tap_to_pay: 'Tap to pay',
  scan_to_pay: 'Scan to pay',
  card_swipe: 'Card swipe',
  mobile_wallet: 'Mobile wallet',
}

const INCOME_TYPE_LABELS = {
  eft_received: 'EFT received',
  cash_deposit: 'Cash deposit',
}

export default function TransactionsPage() {
  const { filters, handleSelectStage } = useDashboard()
  const lifecycleStage = filters.lifecycle_stage

  const url = lifecycleStage
    ? `/api/analytics/payment-methods?lifecycle_stage=${lifecycleStage}`
    : '/api/analytics/payment-methods'
  const { data, loading } = useFetch(() => apiGet(url), [url])

  const byMethod = (data?.by_method ?? []).map((row) => ({
    label: PAYMENT_METHOD_LABELS[row.payment_method] ?? row.payment_method,
    count: row.count,
    extra: `R${Math.round(row.total_amount).toLocaleString('en-ZA')}`,
  }))
  const byCardType = (data?.by_card_type ?? []).map((row) => ({
    label: row.card_type,
    count: row.count,
    extra: `R${Math.round(row.total_amount).toLocaleString('en-ZA')}`,
  }))
  const byIndustry = (data?.by_industry ?? []).map((row) => ({ label: row.industry, count: row.count }))
  const byIncomeType = (data?.by_income_type ?? []).map((row) => ({
    label: INCOME_TYPE_LABELS[row.income_type] ?? row.income_type,
    count: row.count,
    extra: `R${Math.round(row.total_amount).toLocaleString('en-ZA')}`,
  }))

  return (
    <>
      <h1 className="page-title">Transactions</h1>
      <p className="page-subtitle">How customers pay, and which accounts are seeing activity</p>

      <div className="grid-row">
        <LifecycleChart
          byStage={data?.by_lifecycle_stage}
          selectedStage={lifecycleStage}
          onSelectStage={handleSelectStage}
          title="Transactions by lifecycle stage"
          subtitle="click a stage to filter"
        />
        {!loading && (
          <BreakdownChart title="By industry" subtitle="which sectors drive transaction volume" data={byIndustry} color="#eda100" />
        )}
      </div>

      <div className="grid-row">
        {loading ? (
          <p className="panel-empty">Loading&hellip;</p>
        ) : (
          <>
            <BreakdownChart title="By payment method" subtitle="tap, scan, swipe, wallet - POS only" data={byMethod} color="#2a78d6" />
            <BreakdownChart title="By card type" subtitle="debit vs credit - POS only" data={byCardType} color="#01466f" />
          </>
        )}
      </div>

      <div className="grid-row">
        {!loading && (
          <BreakdownChart
            title="Other income"
            subtitle="EFT received and cash deposits - not point-of-sale"
            data={byIncomeType}
            color="#1baf7a"
          />
        )}
        <DenseListPanel
          title="Top accounts"
          subtitle="by POS transaction volume"
          endpoint="/api/analytics/top-accounts"
          limit={5}
          lifecycleStage={lifecycleStage}
          rowsPath="top_accounts"
          renderTag={(row) => `${row.transaction_count} transactions processed`}
          tagTitle="Total POS transactions processed - a proxy for how actively this account uses its POS service"
          emptyText="No accounts yet."
          collapsible
        />
      </div>

      <div className="grid-row">
        <RecordsList
          title="POS transactions"
          endpoint="/api/transactions"
          lifecycleStage={lifecycleStage}
          renderMain={(row) => `${row.transaction_type} · R${Math.round(row.amount).toLocaleString('en-ZA')}`}
          renderTag={(row) => `${PAYMENT_METHOD_LABELS[row.payment_method] ?? row.payment_method}${row.card_type ? ' · ' + row.card_type : ''}`}
          csvFilename="transactions.csv"
          csvRow={(row) => ({
            account_id: row.account_id,
            amount: row.amount,
            transaction_type: row.transaction_type,
            payment_method: row.payment_method,
            card_type: row.card_type,
            merchant: row.merchant,
            transaction_date: row.transaction_date,
          })}
        />

        <RecordsList
          title="Other income (EFT & cash deposits)"
          endpoint="/api/other-income"
          lifecycleStage={lifecycleStage}
          renderMain={(row) => `${INCOME_TYPE_LABELS[row.income_type] ?? row.income_type} · R${Math.round(row.amount).toLocaleString('en-ZA')}`}
          renderTag={(row) => row.account_id}
          csvFilename="other_income.csv"
          csvRow={(row) => ({
            account_id: row.account_id,
            income_type: row.income_type,
            amount: row.amount,
            income_date: row.income_date,
          })}
        />
      </div>
    </>
  )
}
