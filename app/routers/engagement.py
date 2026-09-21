"""
Engagement Metrics Router
Handles WAU (Weekly Active User) and MAU (Monthly Active User) endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/accounts", tags=["Engagement"])


@router.get("/{account_id}/wau", response_model=list[schemas.WAUResponse])
@limiter.limit("30/minute")
def get_account_wau(request: Request, account_id: str, db: Session = Depends(get_db)):
    """Get Weekly Active User data for account (first 4 weeks)."""
    wau_records = db.query(models.WeeklyActiveUser).filter(
        models.WeeklyActiveUser.account_id == account_id
    ).all()

    if not wau_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No WAU data found for {account_id}"
        )

    return wau_records


@router.get("/{account_id}/mau", response_model=list[schemas.MAUResponse])
@limiter.limit("30/minute")
def get_account_mau(request: Request, account_id: str, db: Session = Depends(get_db)):
    """Get Monthly Active User data for account (after week 4)."""
    mau_records = db.query(models.MonthlyActiveUser).filter(
        models.MonthlyActiveUser.account_id == account_id
    ).all()

    if not mau_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No MAU data found for {account_id}"
        )

    return mau_records
