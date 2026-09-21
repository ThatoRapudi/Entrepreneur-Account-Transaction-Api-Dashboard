"""
FastAPI Application Entry Point (RESTRUCTURED)
Registers all routers - business logic lives in app/routers/
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi import Depends
from app.database import engine, Base
from app.config import settings
from app.middleware.rate_limiter import limiter
from app.auth import get_current_user
from app.routers import accounts, transactions, insurance, loans, engagement, analytics, auth, other_income


# ============================================================================
# CREATE DATABASE TABLES
# ============================================================================

Base.metadata.create_all(bind=engine)


# ============================================================================
# INITIALIZE FASTAPI APP
# ============================================================================

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Entrepreneur Account Aggregation API - Track business engagement",
    openapi_version="3.1.0"
)


# ============================================================================
# CORS (Cross-Origin Resource Sharing)
# ============================================================================
# The React dashboard runs on its own dev server (Vite defaults to
# http://localhost:5173) which is a different origin from this API
# (http://localhost:8000). Without CORS, the browser blocks the dashboard's
# fetch requests entirely.
#
# Vite picks a different port than 5173 whenever 5173 is already taken
# (5174, 5175, ...) - a hardcoded allowlist of exact origins broke every
# time that happened ("Disallowed CORS origin", a 400 on the browser's
# preflight OPTIONS request). allow_origin_regex covers any localhost or
# 127.0.0.1 port instead - that keeps working in dev/Docker Compose
# regardless of port. FRONTEND_URL (set in .env once there's a real
# deployed frontend) is added on top via allow_origins, so production
# isn't stuck on the localhost-only regex.

_allowed_origins = [origin.strip() for origin in settings.FRONTEND_URL.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================================
# RATE LIMITING
# ============================================================================
# app.state.limiter makes the shared limiter available to every request.
# The exception handler returns a clean 429 response (with Retry-After)
# instead of an unhandled error when a client exceeds its limit.

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# REGISTER ROUTERS
# ============================================================================

# auth.router is intentionally unprotected - it's the endpoint that
# issues the token everything else here requires.
app.include_router(auth.router)

# Every other router sits behind the login gate: a request with no
# valid bearer token never reaches the route function at all.
_protected = [Depends(get_current_user)]
app.include_router(accounts.router, dependencies=_protected)
app.include_router(transactions.router, dependencies=_protected)
app.include_router(insurance.router, dependencies=_protected)
app.include_router(loans.router, dependencies=_protected)
app.include_router(engagement.router, dependencies=_protected)
app.include_router(analytics.router, dependencies=_protected)
app.include_router(other_income.router, dependencies=_protected)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health", tags=["System"])
def health_check():
    """Simple endpoint to verify API is running."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.API_VERSION
    }


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["System"])
def root():
    """Root endpoint - provides API information."""
    return {
        "message": f"Welcome to {settings.API_TITLE}",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Runs when API starts."""
    print(f"✓ API starting: {settings.API_TITLE} v{settings.API_VERSION}")
    print(f"✓ Database: {engine.url.get_backend_name()} ({engine.url.database})")
    print(f"✓ Debug mode: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """Runs when API shuts down."""
    print("✓ API shutting down")