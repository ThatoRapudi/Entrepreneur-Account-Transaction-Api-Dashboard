# Production Deployment

How to run the Entrepreneur Account Aggregation API, add data to it, and look inside its database. Every command below works the same whether you're using Command Prompt, PowerShell, or a Mac/Linux terminal.

## Prerequisites

Before getting started, ensure that:

Docker Desktop is installed.
Docker Desktop is running.
You have cloned the project locally.

## Run it

You need Docker Desktop installed and open. Then:

1. Open a terminal and go to the project folder.
2. Run this command:

```
docker compose up --build
```

3. Wait for it to finish starting (a minute or two the first time).
4. Open your browser to `http://localhost:5173` - that's the dashboard. Log in details will be provided.
5. The API itself, and its documentation, is at `http://localhost:8000/docs`.

That's it - nothing to set up or configure first, it just runs.

To stop it, go back to that terminal and press Ctrl+C, or run `docker compose down` from a new one. The data stays saved for next time either way.

If you only changed one part of the code and want to rebuild just that part: `docker compose up --build backend` or `docker compose up --build frontend`.

## Add more data

Once it's running, you can add more mock accounts and transactions with:

```
docker compose exec backend python seed_database.py --add 200 or more
```

That adds 200 new accounts on top of what's already there. If you'd rather wipe everything and start fresh instead, add `--reset`:

```
docker compose exec backend python seed_database.py --reset --add 200
```

## Look inside the database

There are two ways to see or check the actual data being stored.

**Option 1: A quick command-line view**

```
docker compose exec db psql -U entrepreneur_app -d entrepreneur_db
```

Once you're in, a few useful things to type:

```sql
\dt                                    -- see every table
SELECT COUNT(*) FROM accounts;         -- how many accounts exist
SELECT * FROM accounts LIMIT 10;       -- look at the first 10
\q                                     -- exit
```
## Important note

Any changes made directly through PostgreSQL bypass the application's validation rules and business logic.

Direct database access is useful for:

Viewing records
Debugging data
Running queries
Testing database behaviour

For normal usage and data management, it is recommended to use the dashboard or the API endpoints exposed through the application.
