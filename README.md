# Entrepreneur Account Aggregation API

This is the **Entrepreneur Account Aggregation API** - a backend and dashboard built to track entrepreneur accounts from the day they join onward: what stage of their lifecycle they're in (new, early, growing, mature, aged), and how they've been using our services - card payments, other income, loans, and insurance - ever since. It's a FastAPI backend with a React frontend, backed by SQLite for local development and PostgreSQL for anything closer to production.

The project runs with zero setup - no `.env` file to create, no values to fill in. Everything needed to run it is already baked in as safe demo defaults.

## What it does

Card payments, direct EFT/cash income, loans, and insurance used to be separate, disconnected streams with no single view of how an account as a whole was doing. This pulls them together into one place and answers two questions at once for any slice of accounts: what lifecycle stage are they in, and what industry are they in - then breaks down every service's usage across both.

It's built for a small internal team reading dashboards, not thousands of end users - which is why most of the API is pre-aggregated analytics (counts and breakdowns computed in SQL) rather than raw record dumps, and why page sizes are capped server-side no matter how large the underlying data gets.

## Tech stack

**Backend:** FastAPI, SQLAlchemy, Pydantic, JWT login gate, rate limiting via `slowapi`. SQLite locally, PostgreSQL when containerized, gunicorn managing the app in production.

**Frontend:** React (Vite), `react-router-dom`, Recharts for the charts, plain CSS for layout.

**Infrastructure:** Docker Compose runs Postgres, the backend, and the frontend together - see below.

## How it's put together

The backend and frontend are a classic client-server split: the API owns the database, every business rule, and authentication; the frontend only renders and calls the API for real data. They're connected by one contract - the JSON shape of each endpoint, defined once with Pydantic and consumed by the frontend's fetch calls.

A few design choices worth calling out, since they came from actually working through this project's constraints rather than defaults: lifecycle stage and account-ID generation are each computed in exactly one place and reused everywhere, after an earlier bug where the same logic lived in two spots and drifted apart. The login is a lightweight JWT gate rather than full SSO - a deliberate scoping choice for a single-admin internal dashboard, not a shortcut hiding a bigger gap. Moving from SQLite to Postgres surfaced one real incompatibility (a SQLite-only date function), fixed and confirmed against both databases rather than assumed. And several near-duplicate chart/list components got consolidated into a handful of reusable ones, so a shared feature only has to be built once.

On the code structure itself: the backend keeps routers (request handling), models (the database schema), and schemas (the API's request/response contract) as separate layers, with two "single source of truth" helper modules for lifecycle stage and account numbering. The frontend mirrors that with reusable chart/list components shared across every page, and two React Context providers for session and shared filter state. Full details on any of this are best explored in the code itself - it's organized by responsibility, one concern per file.

## Running it

```bash
docker compose up --build
```

No setup needed. Once it's up:

- Dashboard: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

To add more mock data once it's running: `docker compose exec backend python seed_database.py --add 200` (add `--reset` first to wipe and start over instead).

Prefer running it without Docker? `pip install -r requirements.txt && uvicorn app.main:app --reload` for the backend, and `cd frontend && npm install && npm run dev` for the frontend, in two terminals.

See [`PRODUCTION_DEPLOYMENT.md`](./PRODUCTION_DEPLOYMENT.md) for the deeper deployment notes - what would need to change for an actual production deployment, how to inspect the database directly, and the full production-readiness audit.
