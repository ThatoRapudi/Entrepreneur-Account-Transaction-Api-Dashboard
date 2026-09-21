"""
POS Transaction Router
Handles all transaction-related endpoints (CRUD, filtering, pagination)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.utils.pagination import PaginationParams
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.post("/pos", response_model=schemas.POSTransactionResponse)
@limiter.limit("60/minute")
def record_pos_transaction(
    request: Request,
    transaction: schemas.POSTransactionCreate,
    db: Session = Depends(get_db)
):
    """Record a POS transaction (card swipe)."""
    account = db.query(models.Account).filter(
        models.Account.account_id == transaction.account_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {transaction.account_id} not found"
        )

    transaction_id = f"TXN-{datetime.utcnow().timestamp()}"

    db_transaction = models.POSTransaction(
        account_id=transaction.account_id,
        transaction_id=transaction_id,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        description=transaction.description,
        merchant=transaction.merchant,
        payment_method=transaction.payment_method,
        card_type=transaction.card_type,
        transaction_date=datetime.utcnow()
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction


@router.get("", response_model=list[schemas.POSTransactionResponse])
@limiter.limit("30/minute")
def list_transactions(
    request: Request,
    account_id: str = None,
    lifecycle_stage: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """Get transactions with optional filtering and pagination."""
    query = db.query(models.POSTransaction)

    if account_id:
        query = query.filter(models.POSTransaction.account_id == account_id)

    if lifecycle_stage:
        query = query.join(
            models.Account, models.Account.account_id == models.POSTransaction.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)

    # Most recent transaction first - "recent activity" only means
    # something if this is actually ordered by when it happened.
    query = query.order_by(models.POSTransaction.transaction_date.desc())

    pagination = PaginationParams(page, page_size)
    query = pagination.apply(query)

    transactions = query.all()
    return transactions


@router.get("/{transaction_id}", response_model=schemas.POSTransactionResponse)
@limiter.limit("60/minute")
def get_transaction(request: Request, transaction_id: str, db: Session = Depends(get_db)):
    """Get specific transaction by transaction_id."""
    transaction = db.query(models.POSTransaction).filter(
        models.POSTransaction.transaction_id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )

    return transaction


@router.put("/{transaction_id}", response_model=schemas.POSTransactionResponse)
@limiter.limit("20/minute")
def update_transaction(
    request: Request,
    transaction_id: str,
    transaction_update: schemas.POSTransactionCreate,
    db: Session = Depends(get_db)
):
    """Update a POS transaction."""
    transaction = db.query(models.POSTransaction).filter(
        models.POSTransaction.transaction_id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found"
        )

    transaction.amount = transaction_update.amount
    transaction.transaction_type = transaction_update.transaction_type
    transaction.description = transaction_update.description
    transaction.merchant = transaction_update.merchant
    transaction.payment_method = transaction_update.payment_method
    transaction.card_type = transaction_update.card_type

    db.commit()
    db.refresh(transaction)

    return transaction
