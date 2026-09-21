"""
One-time data migration: copies every row from the existing SQLite
database (entrepreneur.db) into a Postgres database, table by table,
preserving primary keys - so existing account_id values, foreign keys,
and anything already linked to a specific row keeps working after the
switch to Postgres.

Usage:
    python migrate_sqlite_to_postgres.py \\
        --source sqlite:///./entrepreneur.db \\
        --target postgresql://entrepreneur_app:PASSWORD@localhost:5432/entrepreneur_db

Run this AFTER the Postgres database exists and is reachable (e.g.
after `docker compose up db`), and BEFORE pointing the live app's
DATABASE_URL at it.

Safe to run against an empty target database - it creates the schema
itself. NOT safe to run twice against a target that already has data:
it doesn't check for existing rows, and a second run will fail on
unique-constraint violations. If you need to redo it, drop and recreate
the target database first.
"""
import argparse
import sys

from sqlalchemy import create_engine, select, text

from app import models  # noqa: F401 - import populates Base.metadata with every table
from app.database import Base


def migrate(source_url: str, target_url: str, batch_size: int = 1000):
    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url)

    print(f"Source: {source_engine.url}")
    print(f"Target: {target_engine.url}")

    print("Creating schema on target (safe if it already exists)...")
    Base.metadata.create_all(bind=target_engine)

    # sorted_tables respects foreign key dependencies - accounts is
    # created and copied before any table with an account_id FK, so
    # nothing ever references a row that doesn't exist yet.
    tables = Base.metadata.sorted_tables
    is_postgres_target = target_engine.url.get_backend_name() == "postgresql"

    with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
        for table in tables:
            rows = source_conn.execute(select(table)).mappings().all()
            if not rows:
                print(f"  {table.name}: 0 rows, skipping")
                continue

            print(f"  {table.name}: copying {len(rows)} rows...")
            for start in range(0, len(rows), batch_size):
                batch = [dict(row) for row in rows[start:start + batch_size]]
                target_conn.execute(table.insert(), batch)
            target_conn.commit()

            # Postgres SERIAL/IDENTITY columns track their own next-value
            # counter separately from the data itself - copying rows in
            # with explicit id values doesn't advance that counter, so
            # the very next INSERT without an explicit id (i.e. anything
            # the live app creates afterward) could collide with one of
            # the ids just copied in. Bump the sequence to match.
            if is_postgres_target and "id" in table.c:
                target_conn.execute(text(
                    f"SELECT setval("
                    f"pg_get_serial_sequence('{table.name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table.name}), 1))"
                ))
                target_conn.commit()

    print("\nDone. Spot-check a few row counts against the source before relying on this:")
    print("  SELECT COUNT(*) FROM accounts;  -- compare against the SQLite count")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default="sqlite:///./entrepreneur.db", help="Source DATABASE_URL (default: the local entrepreneur.db)")
    parser.add_argument("--target", required=True, help="Target Postgres DATABASE_URL to migrate into")
    args = parser.parse_args()

    if "sqlite" in args.target:
        print("--target looks like a SQLite URL, not Postgres - did you mean to swap --source and --target?")
        sys.exit(1)

    migrate(args.source, args.target)
