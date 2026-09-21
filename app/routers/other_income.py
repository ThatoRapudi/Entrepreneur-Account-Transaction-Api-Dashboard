"""
Other Income Router
Non-POS income: EFT payments received from other businesses/clients,
and direct cash deposits - see app/models.py's OtherIncome docstring
for why this is its own table rather than folded into POSTransaction.

Read-only for now (list + get) - there's no live "record a deposit"
flow in the dashboard yet, only mock data via seed_database.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.pagination import PaginationParams
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/other-income", tags=["Other Income"])


@router.get("", response_model=list[schemas.OtherIncomeResponse])
@limiter.limit("30/minute")
def list_other_income(
    request: Request,
    account_id: str = None,
    lifecycle_stage: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """Get other-income records (EFT received / cash deposits) with optional filtering and pagination."""
    query = db.query(models.OtherIncome)

    if account_id:
        query = query.filter(models.OtherIncome.account_id == account_id)

    if lifecycle_stage:
        query = query.join(
            models.Account, models.Account.account_id == models.OtherIncome.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)

    query = query.order_by(models.OtherIncome.income_date.desc())

    pagination = PaginationParams(page, page_size)
    query = pagination.apply(query)

    return query.all()


@router.get("/{income_id}", response_model=schemas.OtherIncomeResponse)
@limiter.limit("60/minute")
def get_other_income(request: Request, income_id: str, db: Session = Depends(get_db)):
    """Get a specific other-income record by income_id."""
    record = db.query(models.OtherIncome).filter(
        models.OtherIncome.income_id == income_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Other income record {income_id} not found"
        )

    return record
