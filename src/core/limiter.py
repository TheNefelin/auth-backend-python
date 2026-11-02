"""Rate limiter module for the Auth Unificado backend.

Provides rate limiting functionality for API endpoints.
"""

import time
from collections import defaultdict
from typing import defaultdict as _defaultdict


# In-memory rate limiter (for production, use Redis or dedicated service)
_rate_limits: _defaultdict[str, list] = _defaultdict(list)


class RateLimitExceeded(HTTPException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=429,
            detail="Rate limit exceeded",
        )
        self.retry_after = retry_after


def check_rate_limit(
    identifier: str,
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
) -> bool:
    """Check if the identifier is within rate limits.
    
    Returns True if within limits, False if exceeded.
    """
    now = time.time()
    minute_ago = now - 60
    hour_ago = now - 3600
    
    # Clean old entries
    _rate_limits[identifier] = [
        timestamp for timestamp in _rate_limits[identifier]
        if timestamp > minute_ago
    ]
    _rate_limits[f"{identifier}:hour"] = [
        timestamp for timestamp in _rate_limits[f"{identifier}:hour"]
        if timestamp > hour_ago
    ]
    
    # Check minute limit
    minute_count = len(_rate_limits[identifier])
    if minute_count >= requests_per_minute:
        return False
    
    # Check hour limit
    hour_count = len(_rate_limits[f"{identifier}:hour"])
    if hour_count >= requests_per_hour:
        return False
    
    # Record current request
    _rate_limits[identifier].append(now)
    _rate_limits[f"{identifier}:hour"].append(now)
    
    return True