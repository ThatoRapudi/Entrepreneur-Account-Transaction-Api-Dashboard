# SQLAlchemy ORM Models - Database Tables
# Each class  is one database table

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Account(Base):
    # Main entrepreneurial account table.
    # Stores business account information.
    
    # Why this table- Core entity: we track everything for this account

    __tablename__ = "accounts"
    
    # Columns (fields in the table)
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), unique=True, index=True)
    business_name = Column(String(255), nullable=False)
    owner_name = Column(String(255), nullable=False)
    # Indexed: all four are filtered/grouped-by constantly across the
    # analytics endpoints (lifecycle donut, industry breakdown, date-
    # range trends) - without an index those are full table scans.
    industry = Column(String(100), nullable=False, index=True)
    opening_date = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50), default="active", index=True)
    lifecycle_stage = Column(String(50), default="beginning", index=True)
    days_since_open = Column(Integer, default=0)
    churn_risk_score = Column(Float, default=0.0)
    # Estimated monthly turnover (rand), banded by lifecycle stage at
    # seed time - the "how big is this business" figure. Separate from
    # the actual recorded revenue (POS transactions + other income),
    # which is what actually happened rather than an estimate.
    monthly_turnover = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (links to other tables)
    wau_records = relationship("WeeklyActiveUser", back_populates="account")
    mau_records = relationship("MonthlyActiveUser", back_populates="account")
    pos_transactions = relationship("POSTransaction", back_populates="account")
    insurance_policies = relationship("InsurancePolicy", back_populates="account")
    loans = relationship("Loan", back_populates="account")
    other_income = relationship("OtherIncome", back_populates="account")


class WeeklyActiveUser(Base):
    # Tracks engagement during first 4 weeks (new account phase).
    
    # Why this table:
    # Measure early adoption: is the account being used?
    # Example: Week 1, account opened 47 times, used 2 services
    # Purpose is to identify dormant accounts early
    __tablename__ = "weekly_active_users"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), ForeignKey("accounts.account_id"), index=True)
    week_number = Column(Integer)  # 1, 2, 3, or 4
    usage_count = Column(Integer, default=0)  # How many times opened
    is_active = Column(Boolean, default=False)  # True if usage_count >= 1
    services_used = Column(JSON, default=list)  # ["POS", "Insurance"]
    first_service_date = Column(DateTime, nullable=True)
    most_used_service = Column(String(100), nullable=True)
    adoption_rate = Column(Float, default=0.0)  # % of services used
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("Account", back_populates="wau_records")


class MonthlyActiveUser(Base):
    # Tracks engagement after week 4 (established account phase).
    # Why this table:
    # Measure long-term health: are they still using services?
    # Example: August 2026, 156 total interactions, peak day = Monday
    #Helps predict churn and retention
    __tablename__ = "monthly_active_users"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), ForeignKey("accounts.account_id"), index=True)
    month = Column(String(7))  # Format: "2026-08"
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=False)
    services_used = Column(JSON, default=list)
    peak_usage_day = Column(String(10), nullable=True)  # "Monday", "Tuesday"
    peak_usage_time = Column(String(50), nullable=True)  # "9AM-11AM"
    adoption_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("Account", back_populates="mau_records")


class POSTransaction(Base):
    # Point of Sale transactions (card swipes).
    # Why this table:
    # Track POS service usage: core revenue driver
    # Example: Customer buys airtime via POS machine
    # Helps identify high-revenue accounts
    __tablename__ = "pos_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), ForeignKey("accounts.account_id"), index=True)
    transaction_id = Column(String(100), unique=True, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50))  # "airtime", "electricity", "voucher"
    description = Column(String(255))
    merchant = Column(String(255))
    # How the customer paid at checkout - separate from transaction_type
    # above, which is WHAT was bought, not HOW it was paid for.
    payment_method = Column(String(50), nullable=True, index=True)  # tap_to_pay, scan_to_pay, card_swipe, mobile_wallet
    card_type = Column(String(20), nullable=True, index=True)  # debit, credit - null for scan_to_pay (account-linked, not card-linked)
    transaction_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="pos_transactions")


class InsurancePolicy(Base):
    """
    Insurance product adoption.
    
    Why this table:
    - Track cross-sell: who adopted insurance after POS?
    - Example: Account opens policy on day 15
    - Helps measure product adoption sequence
    """
    __tablename__ = "insurance_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), ForeignKey("accounts.account_id"), index=True)
    policy_id = Column(String(100), unique=True, index=True)
    policy_type = Column(String(100), index=True)  # "business", "liability"
    status = Column(String(50))  # "active", "pending", "expired"
    application_date = Column(DateTime, default=datetime.utcnow, index=True)
    activation_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("Account", back_populates="insurance_policies")


class Loan(Base):
    # Loan product tracking.
    # Why this table- Track credit products: high-value cross-sell
    # Example: Account applies for loan on day 30
    # Helps measure business growth trajectory
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), ForeignKey("accounts.account_id"), index=True)
    loan_id = Column(String(100), unique=True, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(50)) # "applied", "approved", "disbursed", "repaid"
    qualified = Column(Boolean, default=None)
    # short_term (1-6mo), medium_term (7-24mo), long_term (25-60mo) -
    # term_months is the exact value; loan_term is the band it falls in.
    loan_term = Column(String(20), nullable=True, index=True)
    term_months = Column(Integer, nullable=True)
    application_date = Column(DateTime, default=datetime.utcnow, index=True)
    approval_date = Column(DateTime, nullable=True)
    disbursement_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="loans")


class OtherIncome(Base):
    """
    Non-POS income: EFT payments received from other businesses/clients,
    and direct cash deposits.

    Why this table:
    - Not every small business lives on card-present POS sales - a
      wedding planner or a supplier is far more likely to be paid by
      bank transfer against an invoice, or to bank cash directly, than
      to have someone tap a card at their premises.
    - Without this, "turnover" for those accounts would be understated,
      since POSTransaction alone can't represent that income.
    - Kept as its own table (not folded into POSTransaction) because
      it isn't a point-of-sale event at all - no merchant/payment
      method/card type applies.
    """
    __tablename__ = "other_income"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), ForeignKey("accounts.account_id"), index=True)
    income_id = Column(String(100), unique=True, index=True)
    income_type = Column(String(50))  # "eft_received", "cash_deposit"
    amount = Column(Float, nullable=False)
    income_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="other_income")