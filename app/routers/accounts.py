"""
Account Management Router
Handles all account-related endpoints (CRUD, filtering, pagination)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app import models, schemas
from app.utils.pagination import PaginationParams
from app.middleware.rate_limiter import limiter
from app.lifecycle import classify_lifecycle_stage
from app.account_numbers import format_account_id, next_account_number

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post("", response_model=schemas.AccountResponse)
@limiter.limit("20/minute")
def create_account(request: Request, account: schemas.AccountCreate, db: Session = Depends(get_db)):
    """Create a new entrepreneurial account."""
    account_id = format_account_id(next_account_number(db))

    # A brand-new account is always day 0 - classify_lifecycle_stage(0)
    # resolves to "brand_new", not a separate hardcoded default that can
    # drift out of sync with the actual age-based rule everywhere else.
    db_account = models.Account(
        account_id=account_id,
        business_name=account.business_name,
        owner_name=account.owner_name,
        industry=account.industry,
        status=account.status,
        lifecycle_stage=classify_lifecycle_stage(0),
        opening_date=datetime.utcnow(),
        days_since_open=0
    )

    db.add(db_account)
    db.commit()
    db.refresh(db_account)

    return db_account


@router.get("", response_model=list[schemas.AccountResponse])
@limiter.limit("30/minute")
def list_accounts(
    request: Request,
    lifecycle_stage: str = None,
    status_filter: str = None,
    opened_after: str = None,
    opened_before: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get accounts with optional filtering and pagination.

    Query parameters:
    - lifecycle_stage: brand_new, early, growing, mature, aged
    - status_filter: active, inactive
    - opened_after: YYYY-MM-DD format
    - opened_before: YYYY-MM-DD format
    - page: Page number (default: 1)
    - page_size: Records per page (default: 50, max: 100)
    """

    query = db.query(models.Account)

    if lifecycle_stage:
        valid_stages = ["brand_new", "early", "growing", "mature", "aged"]
        if lifecycle_stage not in valid_stages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid lifecycle_stage. Must be one of: {', '.join(valid_stages)}"
            )
        query = query.filter(models.Account.lifecycle_stage == lifecycle_stage)

    if status_filter:
        valid_statuses = ["active", "inactive"]
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        query = query.filter(models.Account.status == status_filter)

    if opened_after:
        try:
            after_date = datetime.strptime(opened_after, "%Y-%m-%d")
            query = query.filter(models.Account.opening_date >= after_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="opened_after must be in format YYYY-MM-DD"
            )

    if opened_before:
        try:
            # opened_before names a calendar day, but opening_date carries
            # a time-of-day - parsing to midnight and filtering <= that
            # instant would silently exclude every account opened later
            # that same day. Push the boundary to the start of the next
            # day instead, so the named day is fully included.
            before_date = datetime.strptime(opened_before, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(models.Account.opening_date < before_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="opened_before must be in format YYYY-MM-DD"
            )

    # Most recently opened accounts first - without this, SQLite returns
    # rows in whatever order the storage engine happens to have them in,
    # which isn't guaranteed to mean anything to a reader.
    query = query.order_by(models.Account.opening_date.desc())

    pagination = PaginationParams(page, page_size)
    query = pagination.apply(query)

    accounts = query.all()

    if not accounts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No accounts found matching filters"
        )

    return accounts


@router.get("/{account_id}", response_model=schemas.AccountResponse)
@limiter.limit("60/minute")
def get_account(request: Request, account_id: str, db: Session = Depends(get_db)):
    """Get specific account by account_id."""
    account = db.query(models.Account).filter(
        models.Account.account_id == account_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    return account


@router.put("/{account_id}", response_model=schemas.AccountResponse)
@limiter.limit("20/minute")
def update_account(
    request: Request,
    account_id: str,
    account_update: schemas.AccountUpdate,
    db: Session = Depends(get_db)
):
    """Update an account."""
    account = db.query(models.Account).filter(
        models.Account.account_id == account_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found"
        )

    if account_update.business_name:
        account.business_name = account_update.business_name
    if account_update.status:
        account.status = account_update.status
    if account_update.lifecycle_stage:
        account.lifecycle_stage = account_update.lifecycle_stage

    account.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(account)

    return account
