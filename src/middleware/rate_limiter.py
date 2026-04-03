"""
Centralised rate-limiter instance shared across all route modules.

Usage in a router:
    from middleware.rate_limiter import limiter
    from slowapi.util import get_remote_address
    from fastapi import Request

    @router.post("/login")
    @limiter.limit("10/minute")
    async def login(request: Request, ...):
        ...

The `request: Request` parameter is required by slowapi even when you don't
use it directly in your handler — slowapi reads it to extract the client key.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Key function: rate-limit per client IP address
limiter = Limiter(key_func=get_remote_address, default_limits=[])
