"""
Insurance Policy Router
Handles all insurance-related endpoints (CRUD, filtering, pagination)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.utils.pagination import PaginationParams
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/policies/insurance", tags=["Insurance"])


@router.post("", response_model=schemas.InsurancePolicyResponse)
@limiter.limit("20/minute")
def create_insurance_policy(
    request: Request,
    policy: schemas.InsurancePolicyCreate,
    db: Session = Depends(get_db)
):
    """Create an insurance policy for an account."""
    account = db.query(models.Account).filter(
        models.Account.account_id == policy.account_id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {policy.account_id} not found"
        )

    policy_id = f"POL-{datetime.utcnow().timestamp()}"

    db_policy = models.InsurancePolicy(
        account_id=policy.account_id,
        policy_id=policy_id,
        policy_type=policy.policy_type,
        status=policy.status,
        application_date=datetime.utcnow()
    )

    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)

    return db_policy


@router.get("", response_model=list[schemas.InsurancePolicyResponse])
@limiter.limit("30/minute")
def list_insurance_policies(
    request: Request,
    account_id: str = None,
    lifecycle_stage: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """Get all insurance policies with optional filtering and pagination."""
    query = db.query(models.InsurancePolicy)

    if account_id:
        query = query.filter(models.InsurancePolicy.account_id == account_id)

    if lifecycle_stage:
        query = query.join(
            models.Account, models.Account.account_id == models.InsurancePolicy.account_id
        ).filter(models.Account.lifecycle_stage == lifecycle_stage)

    query = query.order_by(models.InsurancePolicy.application_date.desc())

    pagination = PaginationParams(page, page_size)
    query = pagination.apply(query)

    policies = query.all()
    return policies


@router.get("/{policy_id}", response_model=schemas.InsurancePolicyResponse)
@limiter.limit("60/minute")
def get_insurance_policy(request: Request, policy_id: str, db: Session = Depends(get_db)):
    """Get specific insurance policy by policy_id."""
    policy = db.query(models.InsurancePolicy).filter(
        models.InsurancePolicy.policy_id == policy_id
    ).first()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found"
        )

    return policy


@router.put("/{policy_id}", response_model=schemas.InsurancePolicyResponse)
@limiter.limit("20/minute")
def update_insurance_policy(
    request: Request,
    policy_id: str,
    policy_update: schemas.InsurancePolicyUpdate,
    db: Session = Depends(get_db)
):
    """Update an insurance policy."""
    policy = db.query(models.InsurancePolicy).filter(
        models.InsurancePolicy.policy_id == policy_id
    ).first()

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found"
        )

    if policy_update.policy_type:
        policy.policy_type = policy_update.policy_type
    if policy_update.status:
        policy.status = policy_update.status
        if policy_update.status == "active":
            policy.activation_date = datetime.utcnow()

    db.commit()
    db.refresh(policy)

    return policy
