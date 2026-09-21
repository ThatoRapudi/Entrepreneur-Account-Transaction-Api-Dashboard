"""
Loan Management Router
Handles all loan-related endpoints (CRUD, filtering, pagination)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.utils.pagination import PaginationParams
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/loans", tags=["Loans"])


@router.post("", response_model=schemas.LoanResponse)
@limiter.limit("20/minute")
def apply_for_loan(
    request: Request,
    loan: schemas.LoanCreate,
    db: Session = Depends(get_db)
):
    """Apply for a loan."""
    account = db.query(models.Account).filter(
        models.Account.account_id == loan.account_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {loan.account_id} not found"
        )

    loan_id = f"LOAN-{datetime.utcnow().timestamp()}"

    db_loan = models.Loan(
        account_id=loan.account_id,
        loan_id=loan_id,
        amount=loan.amount,
        status=loan.status,
        loan_term=loan.loan_term,
        term_months=loan.term_months,
        application_date=datetime.utcnow()
    )

    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)

    return db_loan


@router.get("", response_model=list[schemas.LoanResponse])
@limiter.limit("30/minute")
def list_loans(
    request: Request,
    account_id: str = None,
    lifecycle_stage: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """Get all loans with optional filtering and pagination."""
    query = db.query(models.Loan)

    if account_id:
        query = query.filter(models.Loan.account_id == account_id)

    if lifecycle_stage:
        query = query.join(
            models.Account, models.Account.account_id == models.Loan.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)

    query = query.order_by(models.Loan.application_date.desc())

    pagination = PaginationParams(page, page_size)
    query = pagination.apply(query)

    loans = query.all()
    return loans


@router.get("/{loan_id}", response_model=schemas.LoanResponse)
@limiter.limit("60/minute")
def get_loan(request: Request, loan_id: str, db: Session = Depends(get_db)):
    """Get specific loan by loan_id."""
    loan = db.query(models.Loan).filter(
        models.Loan.loan_id == loan_id
    ).first()

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan {loan_id} not found"
        )

    return loan


@router.put("/{loan_id}", response_model=schemas.LoanResponse)
@limiter.limit("20/minute")
def update_loan(
    request: Request,
    loan_id: str,
    loan_update: schemas.LoanUpdate,
    db: Session = Depends(get_db)
):
    """Update a loan application or status."""
    loan = db.query(models.Loan).filter(
        models.Loan.loan_id == loan_id
    ).first()

    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan {loan_id} not found"
        )

    if loan_update.amount:
        loan.amount = loan_update.amount
    if loan_update.status:
        loan.status = loan_update.status
        if loan_update.status == "approved":
            loan.approval_date = datetime.utcnow()
        elif loan_update.status == "disbursed":
            loan.disbursement_date = datetime.utcnow()
    if loan_update.qualified is not None:
        loan.qualified = loan_update.qualified
    if loan_update.loan_term:
        loan.loan_term = loan_update.loan_term
    if loan_update.term_months:
        loan.term_months = loan_update.term_months

    db.commit()
    db.refresh(loan)

    return loan
