"""
One-off schema migration for the new payment-method / insurance /
loan-term / turnover / other-income fields, plus the indexes that keep
the breakdown/analytics queries fast as the dataset grows.

Why this exists: Base.metadata.create_all() (used by seed_database.py)
only creates tables that don't exist yet - it never alters an existing
table, so it can't add new columns or new indexes onto your current
accounts, pos_transactions, loans, and insurance_policies tables.
SQLite does support ADD COLUMN and CREATE INDEX directly though, so
this runs both, then calls create_all() to create the brand new
other_income table.

Safe to run more than once - every column and every index is checked
against what already exists first and skipped if it's already there.

Run once, before your next seed/reseed:

    python migrate_schema.py

This only adds columns/tables/indexes - it does not touch or delete
any existing row. Existing accounts/transactions/loans will simply
have NULL in the new columns until you add fresh data (or re-seed)
for them.
"""

from sqlalchemy import inspect, text
from app.database import engine, Base
from app import models  # noqa: F401 - import registers all models on Base


COLUMNS_TO_ADD = {
    "accounts": [
        ("monthly_turnover", "REAL"),
    ],
    "pos_transactions": [
        ("payment_method", "VARCHAR(50)"),
        ("card_type", "VARCHAR(20)"),
    ],
    "loans": [
        ("loan_term", "VARCHAR(20)"),
        ("term_months", "INTEGER"),
    ],
}

# Columns used constantly by the analytics/breakdown endpoints for
# WHERE/GROUP BY/JOIN, which had no index at all until now - at small
# row counts this doesn't matter, but it's the right thing to have in
# place before the dataset grows rather than after it starts to drag.
INDEXES_TO_ADD = {
    "accounts": [
        ("ix_accounts_industry", "industry"),
        ("ix_accounts_status", "status"),
        ("ix_accounts_lifecycle_stage", "lifecycle_stage"),
        ("ix_accounts_opening_date", "opening_date"),
    ],
    "pos_transactions": [
        ("ix_pos_transactions_payment_method", "payment_method"),
        ("ix_pos_transactions_card_type", "card_type"),
        ("ix_pos_transactions_transaction_date", "transaction_date"),
    ],
    "loans": [
        ("ix_loans_loan_term", "loan_term"),
        ("ix_loans_application_date", "application_date"),
    ],
    "insurance_policies": [
        ("ix_insurance_policies_policy_type", "policy_type"),
        ("ix_insurance_policies_application_date", "application_date"),
    ],
}


def add_missing_columns():
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in COLUMNS_TO_ADD.items():
            if table not in existing_tables:
                print(f"  {table}: table doesn't exist yet - create_all() below will create it fresh.")
                continue

            existing_columns = {c["name"] for c in inspector.get_columns(table)}
            for column_name, column_type in columns:
                if column_name in existing_columns:
                    print(f"  {table}.{column_name}: already exists, skipping.")
                    continue
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type}"))
                print(f"  {table}.{column_name}: added.")


def add_missing_indexes():
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, indexes in INDEXES_TO_ADD.items():
            if table not in existing_tables:
                print(f"  {table}: table doesn't exist yet - skipping its indexes for now.")
                continue

            existing_index_names = {ix["name"] for ix in inspector.get_indexes(table)}
            existing_columns = {c["name"] for c in inspector.get_columns(table)}
            for index_name, column_name in indexes:
                if column_name not in existing_columns:
                    print(f"  {table}.{column_name}: column doesn't exist yet, skipping its index.")
                    continue
                if index_name in existing_index_names:
                    print(f"  {index_name}: already exists, skipping.")
                    continue
                conn.execute(text(f"CREATE INDEX {index_name} ON {table} ({column_name})"))
                print(f"  {index_name}: created on {table}.{column_name}.")


if __name__ == "__main__":
    print("Adding new columns to existing tables...")
    add_missing_columns()

    print("\nCreating any new tables (other_income)...")
    Base.metadata.create_all(bind=engine)

    print("\nAdding missing indexes...")
    add_missing_indexes()

    print("\nDone. Existing rows have NULL in the new columns - run "
          "seed_database.py (with or without --reset) to add data that "
          "populates them.")
