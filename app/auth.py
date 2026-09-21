"""
Authentication - a simple JWT login gate.

Why "login gate" and not "SSO": true single sign-on delegates identity to
an external provider (Capitec's own, Okta, Azure AD, etc.), which needs
real IdP credentials and config this project doesn't have. This issues
its own short-lived JWT after checking one admin username/password from
.env - enough to demonstrate a properly protected dashboard without a
live identity provider behind it.

The pieces (python-jose, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES)
were already sitting in requirements.txt/config.py, unused, from the
original scaffold - this is what they were for.
"""

import hmac
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.config import settings

security = HTTPBearer()

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_credentials(username: str, password: str) -> bool:
    """
    Constant-time comparison against the single admin account configured
    in .env (ADMIN_USERNAME / ADMIN_PASSWORD). Plaintext, not hashed -
    acceptable for a one-account demo gate, not for a real multi-user
    login system with its own user table.
    """
    username_ok = hmac.compare_digest(username, settings.ADMIN_USERNAME)
    password_ok = hmac.compare_digest(password, settings.ADMIN_PASSWORD)
    return username_ok and password_ok


def create_access_token(subject: str) -> str:
    """Issue a JWT that expires after ACCESS_TOKEN_EXPIRE_MINUTES."""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency that guards every protected route. Any request missing a
    bearer token, or carrying one that's malformed/expired/signed with
    the wrong key, is rejected with 401 before it reaches the route.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise credentials_exception

    username: Optional[str] = payload.get("sub")
    if username is None:
        raise credentials_exception

    return username
