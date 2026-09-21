"""
Analytics Router
Handles analytics and reporting endpoints
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from app.database import get_db
from app import models
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _day_key(value) -> str:
    """
    Normalizes a grouped-by-day value to a plain 'YYYY-MM-DD' string.

    func.date(col) - unlike func.strftime(), which is SQLite-only - is
    one of the few date functions both dialects support under the same
    name: SQLite's date() returns an ISO text string, Postgres's date()
    (a functional cast, equivalent to col::date) returns a real
    datetime.date via psycopg2. This normalizes both to the same string
    shape instead of assuming either one.

    (An earlier version of this used cast(col, Date) instead, which
    turned out to be the less portable choice: SQLite has no real DATE
    storage class, so CAST(x AS DATE) falls back to NUMERIC affinity and
    silently leaves a full datetime string untouched rather than
    truncating it - confirmed by testing against the real database,
    not just assumed.)
    """
    return value.strftime("%Y-%m-%d") if hasattr(value, "strftime") else str(value)[:10]


@router.get("/summary")
@limiter.limit("10/minute")
def get_summary_analytics(request: Request, days: int = None, db: Session = Depends(get_db)):
    """
    Get overall summary analytics.

    days: accepted for backward compatibility but no longer scopes
    by_lifecycle_stage. Lifecycle stage is a function of how long an
    account has been open (see app/lifecycle.py) - mature and aged
    accounts are, by definition, ones opened well outside any recent
    "last N days" window, so filtering the donut by opening_date >=
    cutoff silently dropped those two stages out of the chart entirely
    whenever a day-range was applied. The donut is a current-state
    snapshot ("what stage is each account in right now"), same as
    active/inactive status below, so it stays all-time regardless of
    the dashboard's day-range dropdown.
    """
    total_accounts = db.query(func.count(models.Account.id)).scalar() or 0
    active_accounts = db.query(func.count(models.Account.id)).filter(
        models.Account.status == "active"
    ).scalar() or 0
    inactive_accounts = total_accounts - active_accounts

    by_stage = db.query(
        models.Account.lifecycle_stage,
        func.count(models.Account.id).label("count")
    ).group_by(models.Account.lifecycle_stage).all()

    total_transactions = db.query(func.count(models.POSTransaction.id)).scalar() or 0

    return {
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "inactive_accounts": inactive_accounts,
        "by_lifecycle_stage": {stage: count for stage, count in by_stage},
        "total_transactions": total_transactions
    }


@router.get("/by-industry")
@limiter.limit("10/minute")
def get_industry_analytics(
    request: Request,
    lifecycle_stage: str = None,
    days: int = None,
    db: Session = Depends(get_db)
):
    """
    Get analytics broken down by industry.

    lifecycle_stage: optional - narrows both counts to accounts in that
    stage, so this panel moves together with the lifecycle donut instead
    of always showing the whole account base.

    days: optional - narrows account_count to accounts opened in the
    last N days, and transaction_count to POS transactions in that same
    window, so this panel moves with the dashboard's day-range dropdown.
    """
    cutoff = None
    if days:
        days = min(max(days, 1), 365)
        cutoff = datetime.utcnow() - timedelta(days=days)

    industries = db.query(models.Account.industry).distinct().all()

    results = []
    for (industry,) in industries:
        account_query = db.query(func.count(models.Account.id)).filter(
            models.Account.industry == industry
        )
        if lifecycle_stage:
            account_query = account_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
        if cutoff:
            account_query = account_query.filter(models.Account.opening_date >= cutoff)
        account_count = account_query.scalar() or 0

        transaction_query = db.query(func.count(models.POSTransaction.id)).join(
            models.Account, models.Account.account_id == models.POSTransaction.account_id
        ).filter(models.Account.industry == industry)
        if lifecycle_stage:
            transaction_query = transaction_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
        if cutoff:
            transaction_query = transaction_query.filter(models.POSTransaction.transaction_date >= cutoff)
        transaction_count = transaction_query.scalar() or 0

        results.append({
            "industry": industry,
            "account_count": account_count,
            "transaction_count": transaction_count
        })

    return {"industries": results}


@router.get("/account/{account_id}/profile")
@limiter.limit("20/minute")
def get_account_profile(request: Request, account_id: str, db: Session = Depends(get_db)):
    """Get detailed profile for a specific account."""
    account = db.query(models.Account).filter(
        models.Account.account_id == account_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    transaction_count = db.query(func.count(models.POSTransaction.id)).filter(
        models.POSTransaction.account_id == account_id
    ).scalar() or 0

    insurance_count = db.query(func.count(models.InsurancePolicy.id)).filter(
        models.InsurancePolicy.account_id == account_id
    ).scalar() or 0

    loan_count = db.query(func.count(models.Loan.id)).filter(
        models.Loan.account_id == account_id
    ).scalar() or 0

    return {
        "account_id": account.account_id,
        "business_name": account.business_name,
        "owner_name": account.owner_name,
        "industry": account.industry,
        "status": account.status,
        "lifecycle_stage": account.lifecycle_stage,
        "days_since_open": account.days_since_open,
        "churn_risk_score": account.churn_risk_score,
        "services": {
            "pos_transactions": transaction_count,
            "insurance_policies": insurance_count,
            "loans": loan_count
        }
    }


@router.get("/top-accounts")
@limiter.limit("10/minute")
def get_top_accounts(
    request: Request,
    limit: int = 10,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Get top accounts by engagement (transaction count).

    lifecycle_stage: optional - restricts the ranking to that stage.
    """
    limit = min(max(limit, 1), 100)

    query = db.query(
        models.Account,
        func.count(models.POSTransaction.id).label("transaction_count")
    ).outerjoin(
        models.POSTransaction,
        models.Account.account_id == models.POSTransaction.account_id
    )

    if lifecycle_stage:
        query = query.filter(models.Account.lifecycle_stage == lifecycle_stage)

    top_accounts = query.group_by(
        models.Account.id
    ).order_by(
        func.count(models.POSTransaction.id).desc()
    ).limit(limit).all()

    return {
        "top_accounts": [
            {
                "account_id": account.account_id,
                "business_name": account.business_name,
                "industry": account.industry,
                "lifecycle_stage": account.lifecycle_stage,
                "transaction_count": count,
                "status": account.status
            }
            for account, count in top_accounts
        ]
    }


@router.get("/accounts-timeseries")
@limiter.limit("10/minute")
def get_accounts_timeseries(
    request: Request,
    days: int = 30,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Daily count of new accounts opened over the last N days.
    Zero-fills days with no accounts so the trend line doesn't skip gaps.
    """
    days = min(max(days, 1), 365)
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = db.query(
        func.date(models.Account.opening_date).label("day"),
        func.count(models.Account.id).label("count")
    ).filter(
        models.Account.opening_date >= cutoff
    )
    if lifecycle_stage:
        query = query.filter(models.Account.lifecycle_stage == lifecycle_stage)
    rows = query.group_by("day").all()

    counts_by_day = {_day_key(day): count for day, count in rows}

    series = []
    for offset in range(days, -1, -1):
        day = (datetime.utcnow() - timedelta(days=offset)).strftime("%Y-%m-%d")
        series.append({"date": day, "count": counts_by_day.get(day, 0)})

    return {"days": days, "series": series}


@router.get("/transactions-timeseries")
@limiter.limit("10/minute")
def get_transactions_timeseries(
    request: Request,
    days: int = 30,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Daily POS transaction volume (count + total amount) over the last N days.
    Zero-fills days with no transactions.
    """
    days = min(max(days, 1), 365)
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = db.query(
        func.date(models.POSTransaction.transaction_date).label("day"),
        func.count(models.POSTransaction.id).label("count"),
        func.sum(models.POSTransaction.amount).label("total_amount")
    ).filter(
        models.POSTransaction.transaction_date >= cutoff
    )
    if lifecycle_stage:
        query = query.join(
            models.Account, models.Account.account_id == models.POSTransaction.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)
    rows = query.group_by("day").all()

    data_by_day = {_day_key(day): (count, total_amount or 0) for day, count, total_amount in rows}

    series = []
    for offset in range(days, -1, -1):
        day = (datetime.utcnow() - timedelta(days=offset)).strftime("%Y-%m-%d")
        count, total_amount = data_by_day.get(day, (0, 0))
        series.append({"date": day, "count": count, "total_amount": round(total_amount, 2)})

    return {"days": days, "series": series}


@router.get("/churn-watchlist")
@limiter.limit("10/minute")
def get_churn_watchlist(
    request: Request,
    limit: int = 10,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Active accounts with the highest churn_risk_score - the accounts most
    worth a check-in call, since churned (inactive) accounts are already lost.

    lifecycle_stage: optional - restricts the watchlist to that stage.
    """
    limit = min(max(limit, 1), 100)

    query = db.query(models.Account).filter(models.Account.status == "active")
    if lifecycle_stage:
        query = query.filter(models.Account.lifecycle_stage == lifecycle_stage)

    accounts = query.order_by(
        models.Account.churn_risk_score.desc()
    ).limit(limit).all()

    return {
        "watchlist": [
            {
                "account_id": a.account_id,
                "business_name": a.business_name,
                "industry": a.industry,
                "lifecycle_stage": a.lifecycle_stage,
                "churn_risk_score": a.churn_risk_score,
                "days_since_open": a.days_since_open,
            }
            for a in accounts
        ]
    }


@router.get("/churned-accounts")
@limiter.limit("10/minute")
def get_churned_accounts(
    request: Request,
    limit: int = 10,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Accounts that have actually churned (status == "inactive") - a
    different list from the watchlist above, which is ACTIVE accounts
    still at risk. Mixing the two together made it hard to tell "may
    churn" apart from "already gone," so they're separate endpoints.

    lifecycle_stage: optional - restricts the list to that stage.
    """
    limit = min(max(limit, 1), 100)

    query = db.query(models.Account).filter(models.Account.status == "inactive")
    if lifecycle_stage:
        query = query.filter(models.Account.lifecycle_stage == lifecycle_stage)

    accounts = query.order_by(
        models.Account.churn_risk_score.desc()
    ).limit(limit).all()

    return {
        "churned_accounts": [
            {
                "account_id": a.account_id,
                "business_name": a.business_name,
                "industry": a.industry,
                "lifecycle_stage": a.lifecycle_stage,
                "churn_risk_score": a.churn_risk_score,
                "days_since_open": a.days_since_open,
            }
            for a in accounts
        ]
    }


@router.get("/adoption-funnel")
@limiter.limit("10/minute")
def get_adoption_funnel(
    request: Request,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Service adoption funnel: Onboarded -> Activated (first POS use) ->
    + Insurance -> + Loans, with churn built into each transition rather
    than shown as a separate number.

    Replaces the old static POS/+Insurance/+Loans product-count funnel,
    which only ever looked at active accounts and couldn't tell you
    anything about the accounts that dropped off along the way. Every
    stage here is cumulative (an account with a loan is also counted as
    activated and insured); dropped_count/churned_count describe the
    step INTO that stage from the previous one - e.g. on "+ Insurance",
    dropped_count is how many activated accounts never added insurance,
    and churned_count is how many of those are now inactive.

    lifecycle_stage: optional - narrows the whole cohort to that stage,
    onboarded count included (so filtering to "brand_new" correctly
    shows 0% insurance/loans - those genuinely haven't happened yet for
    that stage, not a broken chart).
    """
    accounts_query = db.query(models.Account.account_id, models.Account.status)
    if lifecycle_stage:
        accounts_query = accounts_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
    accounts = accounts_query.all()

    all_ids = {a.account_id for a in accounts}
    status_by_id = {a.account_id: a.status for a in accounts}

    def ids_with(model):
        if not all_ids:
            return set()
        rows = db.query(model.account_id).filter(model.account_id.in_(all_ids)).distinct().all()
        return {r[0] for r in rows}

    pos_ids = ids_with(models.POSTransaction)
    insurance_ids = ids_with(models.InsurancePolicy)
    loan_ids = ids_with(models.Loan)

    def churned_count(id_set):
        return sum(1 for i in id_set if status_by_id.get(i) == "inactive")

    funnel = [{
        "stage": "Onboarded",
        "reached_count": len(all_ids),
        "dropped_count": 0,
        "churned_count": 0,
    }]

    for stage_label, reached_ids, previous_ids in [
        ("Activated", pos_ids, all_ids),
        ("+ Insurance", insurance_ids, pos_ids),
        ("+ Loans", loan_ids, insurance_ids),
    ]:
        dropped = previous_ids - reached_ids
        funnel.append({
            "stage": stage_label,
            "reached_count": len(reached_ids),
            "dropped_count": len(dropped),
            "churned_count": churned_count(dropped),
        })

    return {"funnel": funnel}


@router.get("/wau-summary")
@limiter.limit("10/minute")
def get_wau_summary(
    request: Request,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Weekly Active User adoption curve: of accounts in each cohort week
    (1-4, "week 1 of this account's life" - not a calendar week, since
    WeeklyActiveUser.week_number is relative to when the account opened),
    what fraction were actually active. Answers "are new accounts
    actually engaging in their first month?" - the dashboard had no WAU
    view at all before this.
    """
    query = db.query(
        models.WeeklyActiveUser.week_number,
        func.count(models.WeeklyActiveUser.id).label("total"),
        func.sum(func.cast(models.WeeklyActiveUser.is_active, Integer)).label("active")
    )
    if lifecycle_stage:
        query = query.join(
            models.Account, models.Account.account_id == models.WeeklyActiveUser.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)

    rows = query.group_by(models.WeeklyActiveUser.week_number).order_by(
        models.WeeklyActiveUser.week_number
    ).all()

    weeks = []
    for week_number, total, active in rows:
        active = active or 0
        weeks.append({
            "week_number": week_number,
            "active_count": active,
            "total_count": total,
            "active_rate": round((active / total) * 100, 1) if total else 0,
        })

    return {"weeks": weeks}


@router.get("/mau-summary")
@limiter.limit("10/minute")
def get_mau_summary(
    request: Request,
    months: int = 6,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Monthly Active User trend by real calendar month (MonthlyActiveUser.month
    is a "YYYY-MM" string, unlike WAU's per-account cohort week) - how many
    established accounts are still actively using their services, month over
    month. The other long-term-health counterpart to WAU that the dashboard
    was missing entirely.
    """
    months = min(max(months, 1), 24)

    query = db.query(
        models.MonthlyActiveUser.month,
        func.count(models.MonthlyActiveUser.id).label("total"),
        func.sum(func.cast(models.MonthlyActiveUser.is_active, Integer)).label("active"),
        func.avg(models.MonthlyActiveUser.usage_count).label("avg_usage")
    )
    if lifecycle_stage:
        query = query.join(
            models.Account, models.Account.account_id == models.MonthlyActiveUser.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)

    rows = query.group_by(models.MonthlyActiveUser.month).order_by(
        models.MonthlyActiveUser.month.desc()
    ).limit(months).all()

    series = []
    for month, total, active, avg_usage in reversed(rows):
        active = active or 0
        series.append({
            "month": month,
            "active_count": active,
            "total_count": total,
            "active_rate": round((active / total) * 100, 1) if total else 0,
            "avg_usage": round(avg_usage or 0, 1),
        })

    return {"months": months, "series": series}


@router.get("/payment-methods")
@limiter.limit("10/minute")
def get_payment_method_analytics(
    request: Request,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    POS transactions broken down by payment method and by card type,
    plus a by-lifecycle-stage count - powers the Transactions page.

    Also includes a separate by_income_type breakdown of OtherIncome
    (EFT received / cash deposits) - that money moves through the same
    accounts but never has a payment_method/card_type (it's not a
    point-of-sale event), so it's reported as its own breakdown rather
    than folded into by_method, where it wouldn't mean anything.

    lifecycle_stage: optional - narrows every count to accounts in that
    stage, same convention as every other analytics endpoint.
    """
    base_query = db.query(models.POSTransaction)
    if lifecycle_stage:
        base_query = base_query.join(
            models.Account, models.Account.account_id == models.POSTransaction.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)

    method_rows = base_query.with_entities(
        models.POSTransaction.payment_method,
        func.count(models.POSTransaction.id).label("count"),
        func.sum(models.POSTransaction.amount).label("total_amount"),
    ).group_by(models.POSTransaction.payment_method).all()

    card_rows = base_query.filter(models.POSTransaction.card_type.isnot(None)).with_entities(
        models.POSTransaction.card_type,
        func.count(models.POSTransaction.id).label("count"),
        func.sum(models.POSTransaction.amount).label("total_amount"),
    ).group_by(models.POSTransaction.card_type).all()

    stage_query = db.query(
        models.Account.lifecycle_stage,
        func.count(models.POSTransaction.id).label("count")
    ).join(
        models.POSTransaction, models.POSTransaction.account_id == models.Account.account_id
    )
    if lifecycle_stage:
        stage_query = stage_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
    stage_rows = stage_query.group_by(models.Account.lifecycle_stage).all()

    industry_query = db.query(
        models.Account.industry,
        func.count(models.POSTransaction.id).label("count")
    ).join(
        models.POSTransaction, models.POSTransaction.account_id == models.Account.account_id
    )
    if lifecycle_stage:
        industry_query = industry_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
    industry_rows = industry_query.group_by(models.Account.industry).all()

    income_query = db.query(models.OtherIncome)
    if lifecycle_stage:
        income_query = income_query.join(
            models.Account, models.Account.account_id == models.OtherIncome.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)
    income_rows = income_query.with_entities(
        models.OtherIncome.income_type,
        func.count(models.OtherIncome.id).label("count"),
        func.sum(models.OtherIncome.amount).label("total_amount"),
    ).group_by(models.OtherIncome.income_type).all()

    return {
        "by_method": [
            {"payment_method": method, "count": count, "total_amount": round(total or 0, 2)}
            for method, count, total in method_rows
        ],
        "by_card_type": [
            {"card_type": card_type, "count": count, "total_amount": round(total or 0, 2)}
            for card_type, count, total in card_rows
        ],
        "by_lifecycle_stage": {stage: count for stage, count in stage_rows},
        "by_industry": [{"industry": industry, "count": count} for industry, count in industry_rows],
        "by_income_type": [
            {"income_type": income_type, "count": count, "total_amount": round(total or 0, 2)}
            for income_type, count, total in income_rows
        ],
    }


@router.get("/loan-breakdown")
@limiter.limit("10/minute")
def get_loan_breakdown(
    request: Request,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Loans broken down by term (short/medium/long) with count and total/
    average amount per term, plus a by-lifecycle-stage count - powers
    the Loans page.

    lifecycle_stage: optional - narrows every count to accounts in that
    stage, same convention as every other analytics endpoint.
    """
    term_query = db.query(
        models.Loan.loan_term,
        func.count(models.Loan.id).label("count"),
        func.sum(models.Loan.amount).label("total_amount"),
        func.avg(models.Loan.amount).label("avg_amount"),
    )
    if lifecycle_stage:
        term_query = term_query.join(
            models.Account, models.Account.account_id == models.Loan.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)
    term_rows = term_query.group_by(models.Loan.loan_term).all()

    stage_query = db.query(
        models.Account.lifecycle_stage,
        func.count(models.Loan.id).label("count")
    ).join(
        models.Loan, models.Loan.account_id == models.Account.account_id
    )
    if lifecycle_stage:
        stage_query = stage_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
    stage_rows = stage_query.group_by(models.Account.lifecycle_stage).all()

    industry_query = db.query(
        models.Account.industry,
        func.count(models.Loan.id).label("count"),
        func.sum(models.Loan.amount).label("total_amount"),
    ).join(
        models.Loan, models.Loan.account_id == models.Account.account_id
    )
    if lifecycle_stage:
        industry_query = industry_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
    industry_rows = industry_query.group_by(models.Account.industry).all()

    return {
        "by_term": [
            {
                "loan_term": term,
                "count": count,
                "total_amount": round(total or 0, 2),
                "avg_amount": round(avg or 0, 2),
            }
            for term, count, total, avg in term_rows
        ],
        "by_lifecycle_stage": {stage: count for stage, count in stage_rows},
        "by_industry": [
            {"industry": industry, "count": count, "total_amount": round(total or 0, 2)}
            for industry, count, total in industry_rows
        ],
    }


@router.get("/insurance-breakdown")
@limiter.limit("10/minute")
def get_insurance_breakdown(
    request: Request,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Insurance policies broken down by policy type, plus a by-lifecycle-
    stage count - powers the Insurance page.

    lifecycle_stage: optional - narrows every count to accounts in that
    stage, same convention as every other analytics endpoint.
    """
    type_query = db.query(
        models.InsurancePolicy.policy_type,
        func.count(models.InsurancePolicy.id).label("count"),
    )
    if lifecycle_stage:
        type_query = type_query.join(
            models.Account, models.Account.account_id == models.InsurancePolicy.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)
    type_rows = type_query.group_by(models.InsurancePolicy.policy_type).all()

    stage_query = db.query(
        models.Account.lifecycle_stage,
        func.count(models.InsurancePolicy.id).label("count")
    ).join(
        models.InsurancePolicy, models.InsurancePolicy.account_id == models.Account.account_id
    )
    if lifecycle_stage:
        stage_query = stage_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
    stage_rows = stage_query.group_by(models.Account.lifecycle_stage).all()

    industry_query = db.query(
        models.Account.industry,
        func.count(models.InsurancePolicy.id).label("count")
    ).join(
        models.InsurancePolicy, models.InsurancePolicy.account_id == models.Account.account_id
    )
    if lifecycle_stage:
        industry_query = industry_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
    industry_rows = industry_query.group_by(models.Account.industry).all()

    return {
        "by_type": [
            {"policy_type": policy_type, "count": count}
            for policy_type, count in type_rows
        ],
        "by_lifecycle_stage": {stage: count for stage, count in stage_rows},
        "by_industry": [{"industry": industry, "count": count} for industry, count in industry_rows],
    }


@router.get("/top-accounts-insurance")
@limiter.limit("10/minute")
def get_top_accounts_insurance(
    request: Request,
    limit: int = 10,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Top accounts by total insurance policies held, with a breakdown of
    which policy types make up that total - answers "do they cover
    everything, or just one thing (property/vehicle/stock/etc.)?"
    rather than just a raw count like top-accounts does for POS volume.

    lifecycle_stage: optional - restricts the ranking to that stage.
    """
    limit = min(max(limit, 1), 100)

    query = db.query(
        models.Account,
        func.count(models.InsurancePolicy.id).label("policy_count")
    ).join(
        models.InsurancePolicy,
        models.Account.account_id == models.InsurancePolicy.account_id
    )
    if lifecycle_stage:
        query = query.filter(models.Account.lifecycle_stage == lifecycle_stage)

    top = query.group_by(models.Account.id).order_by(
        func.count(models.InsurancePolicy.id).desc()
    ).limit(limit).all()

    account_ids = [account.account_id for account, _ in top]
    types_by_account = {}
    if account_ids:
        type_rows = db.query(
            models.InsurancePolicy.account_id,
            models.InsurancePolicy.policy_type,
            func.count(models.InsurancePolicy.id).label("count")
        ).filter(
            models.InsurancePolicy.account_id.in_(account_ids)
        ).group_by(
            models.InsurancePolicy.account_id, models.InsurancePolicy.policy_type
        ).all()
        for account_id, policy_type, count in type_rows:
            types_by_account.setdefault(account_id, []).append((policy_type, count))

    def format_breakdown(rows):
        rows = sorted(rows, key=lambda r: r[1], reverse=True)
        return " · ".join(f"{count} {ptype}" for ptype, count in rows)

    return {
        "top_accounts": [
            {
                "account_id": account.account_id,
                "business_name": account.business_name,
                "industry": account.industry,
                "lifecycle_stage": account.lifecycle_stage,
                "policy_count": count,
                "policy_breakdown": format_breakdown(types_by_account.get(account.account_id, [])),
            }
            for account, count in top
        ]
    }


@router.get("/activity-summary")
@limiter.limit("10/minute")
def get_activity_summary(
    request: Request,
    days: int = 30,
    lifecycle_stage: str = None,
    db: Session = Depends(get_db)
):
    """
    Grouped counts of what's happened over the last N days, as categories
    rather than a second-by-second feed: new accounts, POS payments, loan
    applications, insurance activations, and other income (EFT/cash
    deposits) received.

    lifecycle_stage: optional - narrows every count to accounts in that stage.
    """
    days = min(max(days, 1), 365)
    cutoff = datetime.utcnow() - timedelta(days=days)

    new_accounts_query = db.query(func.count(models.Account.id)).filter(
        models.Account.opening_date >= cutoff
    )
    if lifecycle_stage:
        new_accounts_query = new_accounts_query.filter(models.Account.lifecycle_stage == lifecycle_stage)
    new_accounts = new_accounts_query.scalar() or 0

    pos_payments_query = db.query(func.count(models.POSTransaction.id)).filter(
        models.POSTransaction.transaction_date >= cutoff
    )
    loans_applied_query = db.query(func.count(models.Loan.id)).filter(
        models.Loan.application_date >= cutoff
    )
    insurance_activated_query = db.query(func.count(models.InsurancePolicy.id)).filter(
        models.InsurancePolicy.status == "active",
        models.InsurancePolicy.application_date >= cutoff
    )
    other_income_query = db.query(func.count(models.OtherIncome.id)).filter(
        models.OtherIncome.income_date >= cutoff
    )
    # Not time-windowed like the counts above - churn has no timestamp of
    # its own, it's a current status. This is "how many are churned right
    # now", not "how many churned in the last N days".
    churned_accounts_query = db.query(func.count(models.Account.id)).filter(
        models.Account.status == "inactive"
    )

    if lifecycle_stage:
        pos_payments_query = pos_payments_query.join(
            models.Account, models.Account.account_id == models.POSTransaction.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)
        loans_applied_query = loans_applied_query.join(
            models.Account, models.Account.account_id == models.Loan.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)
        insurance_activated_query = insurance_activated_query.join(
            models.Account, models.Account.account_id == models.InsurancePolicy.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)
        other_income_query = other_income_query.join(
            models.Account, models.Account.account_id == models.OtherIncome.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)
        churned_accounts_query = churned_accounts_query.filter(
            models.Account.lifecycle_stage == lifecycle_stage
        )

    pos_payments = pos_payments_query.scalar() or 0
    loans_applied = loans_applied_query.scalar() or 0
    insurance_activated = insurance_activated_query.scalar() or 0
    other_income = other_income_query.scalar() or 0
    churned_accounts = churned_accounts_query.scalar() or 0

    return {
        "days": days,
        "new_accounts": new_accounts,
        "pos_payments": pos_payments,
        "loans_applied": loans_applied,
        "insurance_activated": insurance_activated,
        "other_income": other_income,
        "churned_accounts": churned_accounts,
    }
