import time
import logging
from typing import Dict, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimitService:
    """In-memory rate limiting service for notifications"""
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        # Store request timestamps per tenant
        self._request_history: Dict[str, deque] = defaultdict(deque)
        
    def check_rate_limit(self, tenant_id: str) -> bool:
        """
        Check if tenant is within rate limit.
        Returns True if request is allowed, False if rate limited.
        """
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        # Get or create request history for this tenant
        history = self._request_history[tenant_id]
        
        # Remove old requests outside the window
        while history and history[0] < window_start:
            history.popleft()
        
        # Check if we're at the limit
        if len(history) >= self.max_requests:
            logger.warning(
                f"Rate limit exceeded for tenant {tenant_id}: "
                f"{len(history)} requests in last {self.window_seconds}s"
            )
            return False
        
        # Add current request to history
        history.append(current_time)
        
        logger.debug(
            f"Rate limit check passed for tenant {tenant_id}: "
            f"{len(history)}/{self.max_requests} requests in window"
        )
        
        return True
    
    def get_rate_limit_status(self, tenant_id: str) -> Dict[str, any]:
        """Get current rate limit status for a tenant"""
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        history = self._request_history[tenant_id]
        
        # Count requests in current window
        current_requests = sum(1 for timestamp in history if timestamp >= window_start)
        
        # Calculate reset time (when oldest request will expire)
        reset_time = None
        if history:
            oldest_in_window = next((t for t in history if t >= window_start), None)
            if oldest_in_window:
                reset_time = oldest_in_window + self.window_seconds
        
        return {
            "requests_made": current_requests,
            "requests_remaining": max(0, self.max_requests - current_requests),
            "limit": self.max_requests,
            "window_seconds": self.window_seconds,
            "reset_time": reset_time,
            "is_limited": current_requests >= self.max_requests
        }
    
    def reset_tenant_limit(self, tenant_id: str) -> None:
        """Reset rate limit for a specific tenant (admin function)"""
        if tenant_id in self._request_history:
            self._request_history[tenant_id].clear()
            logger.info(f"Rate limit reset for tenant {tenant_id}")
    
    def cleanup_old_entries(self) -> None:
        """Clean up old entries to prevent memory leaks"""
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        tenants_to_remove = []
        
        for tenant_id, history in self._request_history.items():
            # Remove old requests
            while history and history[0] < window_start:
                history.popleft()
            
            # If no recent requests, remove tenant entirely
            if not history:
                tenants_to_remove.append(tenant_id)
        
        for tenant_id in tenants_to_remove:
            del self._request_history[tenant_id]
        
        if tenants_to_remove:
            logger.debug(f"Cleaned up rate limit data for {len(tenants_to_remove)} inactive tenants")

# Global rate limiter instance
rate_limiter = RateLimitService(max_requests=100, window_minutes=1) 