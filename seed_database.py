
#Mock Database Seeder for Entrepreneur Account Aggregation API
import argparse  
import random
import uuid
from datetime import datetime, timedelta

from faker import Faker

from app.database import SessionLocal, engine, Base
from app import models
from app.lifecycle import STAGE_DAY_RANGES, classify_lifecycle_stage
from app.account_numbers import format_account_id, next_account_number

fake = Faker("en_US")

NUM_ACCOUNTS = 50

# The whole mock dataset lives between this date and "today" - no
# account opens before Nov 1, 2025, and lifecycle stage is computed
# from how far back within that window each account's date falls.
EARLIEST_DATE = datetime(2025, 11, 1)

INDUSTRIES = [
    "Online Clothing Retail",
    "Hair & Nails",
    "Catering/Food Services",
    "Wedding Planning & Decor",
    "Spaza Shops",
    "Food Markets",
    "Laundry Services",
]

POS_TRANSACTION_TYPES = [
    {"type": "Mobile Prepaid", "description": "Airtime, Data bundles, Minutes, SMS"},
    {"type": "Utility Bills", "description": "Prepaid electricity, Water"},
    {"type": "Voucher", "description": "Gift voucher, BetWay, Lotto, Electricity vouchers"},
    {"type": "Payment", "description": "Card payment"},
    {"type": "Refund", "description": "Refund Transactions"},
    {"type": "Online Payment", "description": "Apple Pay, Google Pay, PayPal"},
]

#POS payment methods for this customer base are roughly 40% card-present
#(tap), 30% card-not-present (mobile wallet), 20% scan-to-pay, and 10%
#card-present (swipe) - the four values match the ones models.py and
#the frontend's PAYMENT_METHOD_LABELS already know how to label.
PAYMENT_METHODS = ["tap_to_pay", "mobile_wallet", "scan_to_pay", "card_swipe"]
PAYMENT_METHOD_WEIGHTS = [0.40, 0.30, 0.20, 0.10]

# scan_to_pay is account-linked (via an app), not card-linked, so it
# never gets a card_type - every other method rides on a physical or
# tokenized card, which is debit far more often than credit for this
# customer base.
CARD_TYPES = ["debit", "credit"]
CARD_TYPE_WEIGHTS = [0.75, 0.25]


def pick_payment_method():
    method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]
    card_type = None if method == "scan_to_pay" else random.choices(CARD_TYPES, weights=CARD_TYPE_WEIGHTS)[0]
    return method, card_type


# Standard SME insurance spread: cover for the premises, the stock
# inside it, public liability, business equipment (including POS
# devices), and vehicles for the industries that deliver.
INSURANCE_TYPES = ["Property", "Stock/Inventory", "Liability", "Equipment", "Vehicle"]
INSURANCE_TYPE_WEIGHTS = [0.28, 0.28, 0.22, 0.15, 0.07]

# Term band -> (months range, amount range in rand). Short-term loans
# skew toward smaller amounts, long-term toward the R500k cap - term and
# size move together rather than being independent random numbers.
LOAN_TERM_BANDS = [
    {"term": "short_term", "months": (1, 6), "amount": (5_000, 25_000), "weight": 0.45},
    {"term": "medium_term", "months": (7, 24), "amount": (25_000, 200_000), "weight": 0.35},
    {"term": "long_term", "months": (25, 60), "amount": (200_000, 500_000), "weight": 0.20},
]


def pick_loan_term():
    band = random.choices(LOAN_TERM_BANDS, weights=[b["weight"] for b in LOAN_TERM_BANDS])[0]
    months = random.randint(*band["months"])
    amount = float(random.randint(*band["amount"]))
    return band["term"], months, amount


# Estimated monthly turnover (rand) by lifecycle stage - these are all
# small-to-medium businesses (spaza shops, salons, caterers), not large
# operations, so even "aged" tops out well under a million a month.
TURNOVER_RANGES = {
    "brand_new": (5_000, 20_000),
    "early": (15_000, 50_000),
    "growing": (40_000, 150_000),
    "mature": (100_000, 400_000),
    "aged": (80_000, 300_000),
}


def sample_turnover(segment):
    low, high = TURNOVER_RANGES[segment]
    return float(random.randint(low, high))


# Non-POS income: EFT payments received from other businesses/clients,
# and direct cash deposits. Roughly the inverse of LifecycleManager's
# INDUSTRY_RATES below - a wedding planner gets paid by invoice/EFT far
# more than by someone tapping a card, while a spaza shop lives on POS
# and rarely sees a bank transfer.
OTHER_INCOME_RATES = {
    "Wedding Planning & Decor": 2.5,
    "Online Clothing Retail": 1.3,
    "Catering/Food Services": 0.9,
    "Food Markets": 0.5,
    "Laundry Services": 0.5,
    "Hair & Nails": 0.3,
    "Spaza Shops": 0.2,
}
OTHER_INCOME_COUNT_RANGES = {
    "brand_new": (0, 1), "early": (0, 2), "growing": (1, 4), "mature": (2, 8), "aged": (3, 10),
}
OTHER_INCOME_TYPE_WEIGHTS = [0.70, 0.30]  # eft_received, cash_deposit
OTHER_INCOME_AMOUNT_RANGES = {
    "eft_received": (1_000, 50_000),
    "cash_deposit": (500, 15_000),
}


def other_income_count(segment, industry):
    multiplier = OTHER_INCOME_RATES.get(industry, 1.0)
    low, high = OTHER_INCOME_COUNT_RANGES[segment]
    low, high = int(low * multiplier), int(high * multiplier)
    return random.randint(low, high) if high >= low else high


def pick_other_income():
    income_type = random.choices(["eft_received", "cash_deposit"], weights=OTHER_INCOME_TYPE_WEIGHTS)[0]
    low, high = OTHER_INCOME_AMOUNT_RANGES[income_type]
    return income_type, float(random.randint(low, high))

# 50/50 mix of South African and Faker-generated English names, to
# avoid the mock dataset being dominated by either by strictly local or strictly foreign names. 
# #The SA names are drawn from a small sample of common first and last names in South Africa, while Faker generates a wide variety of English names. 
# #This mix provides a more realistic representation of the diverse population in South Africa, where both local and international names are present.
SA_FIRST_NAMES = [
    "Thabo", "Sipho", "Bongani", "Lindiwe", "Nomvula", "Zanele", "Lerato",
    "Kagiso", "Tumelo", "Nthabiseng", "Mandla", "Ayanda", "Nokuthula",
    "Sizwe", "Andile", "Precious", "Palesa", "Boitumelo", "Karabo",
    "Naledi", "Vusi", "Thandiwe", "Nomsa", "Themba", "Zodwa", "Given",
    "Blessing", "Nkosana", "Dumisani", "Refilwe",
]

SA_SURNAMES = [
    "Nkosi", "Dlamini", "Khumalo", "Mokoena", "Mahlangu", "Ndlovu", "Zulu",
    "Sithole", "Mabaso", "Cele", "Buthelezi", "Mthembu", "Radebe", "Nkuna",
    "Molefe", "Tshabalala", "Maluleke", "Mnguni", "Skosana", "Makhanya",
    "Gumede", "Mokone", "Ngcobo", "Vilakazi", "Mokwena", "Sibanda",
    "Motaung", "Mofokeng", "Mahlaba", "Zwane",
]


def random_owner_name():
    """50/50 mix of South African and Faker-generated English names."""
    if random.random() < 0.5:
        return f"{random.choice(SA_FIRST_NAMES)} {random.choice(SA_SURNAMES)}"
    return fake.name()


def first_name_of(full_name):
    return full_name.split()[0]


class LifecycleManager:
    """
    Adoption/churn/pos-volume rates by segment - unchanged in shape from
    before. The day-range-per-stage table itself now lives in
    app/lifecycle.py (STAGE_DAY_RANGES) since the live API needs it too;
    this class only keeps the rates that are specific to mock generation.
    """

    INDUSTRY_RATES = {
        "Spaza Shops": 2.0,
        "Hair & Nails": 1.8,
        "Catering/Food Services": 1.6,
        "Food Markets": 1.6,
        "Laundry Services": 1.4,
        "Online Clothing Retail": 1.0,
        "Wedding Planning & Decor": 0.4,
    }

    CHURN_RATES = {"brand_new": 0.10, "early": 0.15, "growing": 0.05, "mature": 0.02, "aged": 0.01}
    INSURANCE_RATES = {"brand_new": 0.0, "early": 0.15, "growing": 0.40, "mature": 0.70, "aged": 0.85}
    LOAN_RATES = {"brand_new": 0.0, "early": 0.0, "growing": 0.10, "mature": 0.40, "aged": 0.60}
    LOAN_QUALIFICATION_RATES = {"brand_new": 0.10, "early": 0.20, "growing": 0.50, "mature": 0.80, "aged": 0.95}
    POS_COUNT_RANGES = {
        "brand_new": (1, 5), "early": (5, 15), "growing": (20, 50), "mature": (50, 120), "aged": (100, 180),
    }

    @classmethod
    def pos_count(cls, segment, industry):
        multiplier = cls.INDUSTRY_RATES.get(industry, 1.0)
        low, high = cls.POS_COUNT_RANGES[segment]
        return random.randint(int(low * multiplier), int(high * multiplier))


# Target mix across the account base - same 10/20/30/30/10 split used
# before. This decides how likely a random date is to land in each
# stage's window; it's a target, not a hard guarantee, since it's
# ultimately the sampled date that determines the real stage.
STAGE_WEIGHTS = {
    "brand_new": 0.10,
    "early": 0.20,
    "growing": 0.30,
    "mature": 0.30,
    "aged": 0.10,
}


def sample_days_since_open(window_days):
    """
    Pick a target stage per STAGE_WEIGHTS, then a random day count
    within that stage's range (app/lifecycle.py), clamped to how far
    back EARLIEST_DATE actually allows. The stage stored on the account
    is always re-derived from this same day count via
    classify_lifecycle_stage() - never assumed - so the two can't drift.
    """
    stage = random.choices(list(STAGE_WEIGHTS), weights=list(STAGE_WEIGHTS.values()))[0]
    low, high = STAGE_DAY_RANGES[stage]
    high = window_days if high is None else min(high, window_days)
    low = min(low, high)
    return random.randint(low, high) if high >= low else high


def clear_existing_data(db):
    """Delete all rows from every table, respecting FK order (children first)."""
    print("Clearing existing data...")
    db.query(models.WeeklyActiveUser).delete()
    db.query(models.MonthlyActiveUser).delete()
    db.query(models.POSTransaction).delete()
    db.query(models.InsurancePolicy).delete()
    db.query(models.Loan).delete()
    db.query(models.OtherIncome).delete()
    db.query(models.Account).delete()
    db.commit()
    print("  done.\n")



# Probability an account is actually active in a given week/month of
# its life, rather than deriving "is_active" from usage_count and
# hoping it lands on zero. usage_count's old ranges (randint(0,50) for
# WAU, randint(20,300) for MAU) made a zero - and therefore an inactive
# record - vanishingly rare, which is why active_rate always came out
# at ~100% regardless of week or lifecycle stage: it wasn't measuring
# anything, just reporting how unlikely randint(...) was to hit 0.
#
# Weekly rate tapers off - a realistic "onboarding cliff" where some
# fraction of new accounts stop engaging in their first month, which
# is exactly the dormant-account signal WAU is meant to surface.
WEEKLY_ACTIVITY_RATE = {1: 0.85, 2: 0.75, 3: 0.68, 4: 0.60}
# Monthly rate for established accounts - higher and flatter, since by
# this point usage is habitual, but still genuinely not 100%.
MONTHLY_ACTIVITY_RATE = 0.87


def make_wau_records(account_id, days_old):
    """
    Real WAU rows for however many of an account's first 4 weeks it has
    actually lived through - based on its age, not its current
    lifecycle stage, so a now-"growing" or "mature" account still has
    its real week-1-4 history instead of that history simply not
    existing because it aged out of "brand_new"/"early" before this ran.
    """
    weeks_lived = min(days_old // 7, 4)
    records = []
    for week in range(1, weeks_lived + 1):
        is_active = random.random() < WEEKLY_ACTIVITY_RATE[week]
        usage_count = random.randint(1, 50) if is_active else 0
        services = (
            [s for s, p in [("POS", 0.7), ("Insurance", 0.2), ("Loans", 0.1)] if random.random() < p]
            if is_active else []
        )
        records.append({
            "account_id": account_id,
            "week_number": week,
            "usage_count": usage_count,
            "is_active": is_active,
            "services_used": services,
            "adoption_rate": len(services) / 3,
            "created_at": datetime.utcnow(),
        })
    return records


def make_mau_records(account_id, days_old):
    """Real MAU rows for however many of the last 6 months an account has lived through."""
    months_lived = min(days_old // 30, 6)
    records = []
    for month_offset in range(1, months_lived + 1):
        month_date = datetime.utcnow() - timedelta(days=30 * (months_lived - month_offset))
        is_active = random.random() < MONTHLY_ACTIVITY_RATE
        usage_count = random.randint(20, 300) if is_active else 0
        services = (
            [s for s, p in [("POS", 0.8), ("Insurance", 0.5), ("Loans", 0.3)] if random.random() < p]
            if is_active else []
        )
        records.append({
            "account_id": account_id,
            "month": month_date.strftime("%Y-%m"),
            "usage_count": usage_count,
            "is_active": is_active,
            "services_used": services,
            "peak_usage_day": random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
            "peak_usage_time": random.choice(["9AM-11AM", "12PM-2PM", "4PM-6PM"]),
            "adoption_rate": len(services) / 3,
            "created_at": datetime.utcnow(),
        })
    return records


def seed(db, num_accounts=NUM_ACCOUNTS):
    window_days = max((datetime.utcnow() - EARLIEST_DATE).days, 0)

    stats = {"total": 0, "churned": 0, "wau_records": 0, "mau_records": 0,
             "insurance_policies": 0, "loans": 0, "other_income": 0,
             "by_segment": {s: 0 for s in STAGE_DAY_RANGES}}

    accounts_to_insert = []
    transactions_to_insert = []
    wau_to_insert = []
    mau_to_insert = []
    insurance_to_insert = []
    loans_to_insert = []
    other_income_to_insert = []

    # One query to find where the ACC-DDDDDDDDD sequence currently ends
    next_number = next_account_number(db)

    for _ in range(num_accounts):
        days_old = sample_days_since_open(window_days)
        opening_date = datetime.utcnow() - timedelta(days=days_old)
        segment = classify_lifecycle_stage(days_old)  # derived, never assumed

        industry = random.choice(INDUSTRIES)
        owner_name = random_owner_name()
        account_id = format_account_id(next_number)
        next_number += 1
        is_churned = random.random() < LifecycleManager.CHURN_RATES[segment]

        accounts_to_insert.append({
            "account_id": account_id,
            "business_name": f"{first_name_of(owner_name)}'s {industry}",
            "owner_name": owner_name,
            "industry": industry,
            "status": "inactive" if is_churned else "active",
            "lifecycle_stage": segment,
            "opening_date": opening_date,
            "days_since_open": days_old,
            "churn_risk_score": round(random.uniform(60, 95) if is_churned else random.uniform(0, 40), 1),
            "monthly_turnover": sample_turnover(segment),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        stats["total"] += 1
        stats["by_segment"][segment] += 1

        if is_churned:
            stats["churned"] += 1
            continue  # churned accounts get no further activity

        # POS transactions
        for _ in range(LifecycleManager.pos_count(segment, industry)):
            tx_type = random.choice(POS_TRANSACTION_TYPES)
            tx_date = opening_date + timedelta(days=random.randint(0, max(days_old, 1)))
            payment_method, card_type = pick_payment_method()
            transactions_to_insert.append({
                "account_id": account_id,
                "transaction_id": f"TXN-{uuid.uuid4()}",
                "amount": float(random.randint(50, 1000)),
                "transaction_type": tx_type["type"],
                "description": tx_type["description"],
                "merchant": fake.company(),
                "payment_method": payment_method,
                "card_type": card_type,
                "transaction_date": tx_date,
                "created_at": tx_date,
            })

        # Other income: EFT payments received and cash deposits - the
        # revenue POS transactions alone can't represent for accounts
        # paid mostly by invoice/bank transfer rather than card-present
        # sale (see OTHER_INCOME_RATES above).
        for _ in range(other_income_count(segment, industry)):
            income_type, amount = pick_other_income()
            income_date = opening_date + timedelta(days=random.randint(0, max(days_old, 1)))
            other_income_to_insert.append({
                "account_id": account_id,
                "income_id": f"INC-{uuid.uuid4()}",
                "income_type": income_type,
                "amount": amount,
                "income_date": income_date,
                "created_at": income_date,
            })
            stats["other_income"] += 1

        # Real WAU rows for however many of weeks 1-4 this account has
        # actually lived through - age-based, not gated by current
        # stage, so a "growing"/"mature"/"aged" account still carries
        # its real early history instead of that history never existing.
        if days_old >= 7:
            new_wau = make_wau_records(account_id, days_old)
            wau_to_insert.extend(new_wau)
            stats["wau_records"] += len(new_wau)

        # Real MAU rows once an account has at least a month of history.
        if days_old >= 30:
            new_mau = make_mau_records(account_id, days_old)
            mau_to_insert.extend(new_mau)
            stats["mau_records"] += len(new_mau)

        # Insurance adoption
        if random.random() < LifecycleManager.INSURANCE_RATES[segment]:
            insurance_to_insert.append({
                "account_id": account_id,
                "policy_id": f"POL-{uuid.uuid4()}",
                "policy_type": random.choices(INSURANCE_TYPES, weights=INSURANCE_TYPE_WEIGHTS)[0],
                "status": random.choice(["pending", "active"]),
                "application_date": opening_date + timedelta(days=random.randint(0, max(days_old, 1))),
                "created_at": datetime.utcnow(),
            })
            stats["insurance_policies"] += 1

        # Loan adoption - term and amount picked together so the size of
        # the loan lines up with its term instead of being independent
        # random numbers (see LOAN_TERM_BANDS above).
        if random.random() < LifecycleManager.LOAN_RATES[segment]:
            qualified = random.random() < LifecycleManager.LOAN_QUALIFICATION_RATES[segment]
            loan_term, term_months, amount = pick_loan_term()
            loans_to_insert.append({
                "account_id": account_id,
                "loan_id": f"LOAN-{uuid.uuid4()}",
                "amount": amount,
                "status": "applied",
                "qualified": qualified,
                "loan_term": loan_term,
                "term_months": term_months,
                "application_date": opening_date + timedelta(days=random.randint(0, max(days_old, 1))),
                "created_at": datetime.utcnow(),
            })
            stats["loans"] += 1

    print(f"Inserting {len(accounts_to_insert)} accounts...")
    db.bulk_insert_mappings(models.Account, accounts_to_insert)
    db.commit()

    print(f"Inserting {len(transactions_to_insert)} POS transactions...")
    db.bulk_insert_mappings(models.POSTransaction, transactions_to_insert)
    db.commit()

    print(f"Inserting {len(wau_to_insert)} WAU records...")
    db.bulk_insert_mappings(models.WeeklyActiveUser, wau_to_insert)
    db.commit()

    print(f"Inserting {len(mau_to_insert)} MAU records...")
    db.bulk_insert_mappings(models.MonthlyActiveUser, mau_to_insert)
    db.commit()

    print(f"Inserting {len(insurance_to_insert)} insurance policies...")
    db.bulk_insert_mappings(models.InsurancePolicy, insurance_to_insert)
    db.commit()

    print(f"Inserting {len(loans_to_insert)} loans...")
    db.bulk_insert_mappings(models.Loan, loans_to_insert)
    db.commit()

    print(f"Inserting {len(other_income_to_insert)} other-income records...")
    db.bulk_insert_mappings(models.OtherIncome, other_income_to_insert)
    db.commit()

    return stats


def print_summary(stats):
    print("\n" + "=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    print(f"Accounts created:      {stats['total']}")
    print(f"Churned (inactive):    {stats['churned']}")
    print(f"WAU records:           {stats['wau_records']}")
    print(f"MAU records:           {stats['mau_records']}")
    print(f"Insurance policies:    {stats['insurance_policies']}")
    print(f"Loans:                 {stats['loans']}")
    print(f"Other income records:  {stats['other_income']}")
    print("\nBy lifecycle stage:")
    for stage, count in stats["by_segment"].items():
        print(f"  {stage:<12} {count}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add mock data to the entrepreneur accounts database.")
    parser.add_argument(
        "--add", type=int, default=NUM_ACCOUNTS,
        help=f"Number of new accounts to add (default: {NUM_ACCOUNTS})"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Wipe all existing data before seeding. Without this flag, new accounts are added on top of what's already there."
    )
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.reset:
            clear_existing_data(db)
        else:
            existing = db.query(models.Account).count()
            print(f"Keeping {existing} existing account(s) - adding {args.add} more.\n"
                  f"(pass --reset to wipe everything first)\n")

        stats = seed(db, args.add)
        print_summary(stats)
    finally:
        db.close()
