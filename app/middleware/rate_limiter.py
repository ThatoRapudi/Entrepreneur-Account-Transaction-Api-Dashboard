"""
Rate Limiting Configuration
Protects the API from abuse and prevents any single client from
overwhelming the database with excessive requests.

Uses slowapi (a FastAPI/Starlette wrapper around limits) keyed by
client IP address. Each router applies its own per-endpoint limit
on top of the global default below.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# One shared limiter instance used across the whole app.
# key_func=get_remote_address means limits are tracked per client IP.
# default_limits apply to any endpoint that doesn't set its own limit.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/day", "50/hour"]
)
