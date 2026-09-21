"""
Auth Router
Single login endpoint - see app/auth.py for what "login" means here
(a JWT gate, not real SSO).
"""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.auth import create_access_token, verify_credentials
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
def login(request: Request, credentials: LoginRequest):
    """
    Exchange the admin username/password (set in .env) for a JWT.
    Every other endpoint requires this token in an Authorization: Bearer
    header - the frontend's login page is what calls this.
    """
    if not verify_credentials(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(subject=credentials.username)
    return LoginResponse(access_token=token)
