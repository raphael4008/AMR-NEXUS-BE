"""
core/rate_limiter.py — AMR-Nexus Rate Limiting via SlowAPI

SlowAPI wraps limits library and integrates cleanly with FastAPI.
Configured with an in-memory backend (default) — can be swapped to
Redis storage for multi-process deployments by changing the storage URI.

Usage in routes:
    from src.core.rate_limiter import limiter
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    @router.post("/token")
    @limiter.limit("10/minute")
    async def login(request: Request, ...):
        ...

Initialisation in main.py lifespan:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
"""

import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger("amr_nexus.rate_limiter")

# Single limiter instance — shared across all routers
# Uses client IP as the key (get_remote_address)
limiter = Limiter(key_func=get_remote_address)
