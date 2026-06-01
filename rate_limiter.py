import time
from typing import Dict, List

class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.client_requests: Dict[str, List[float]] = {}
        self.last_cleanup = time.time()

    def is_allowed(self, client_ip: str) -> (bool, int):
        now = time.time()
        
        # Periodic cleanup of all expired IPs to prevent memory leaks
        if now - self.last_cleanup > self.window_seconds:
            expired_ips = []
            for ip, ts_list in self.client_requests.items():
                active_ts = [ts for ts in ts_list if now - ts < self.window_seconds]
                if not active_ts:
                    expired_ips.append(ip)
                else:
                    self.client_requests[ip] = active_ts
            for ip in expired_ips:
                del self.client_requests[ip]
            self.last_cleanup = now

        # Initialize or clean up old requests for this IP
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []
        else:
            # Remove timestamps outside the sliding window
            self.client_requests[client_ip] = [
                ts for ts in self.client_requests[client_ip] 
                if now - ts < self.window_seconds
            ]

        if len(self.client_requests[client_ip]) < self.requests_limit:
            self.client_requests[client_ip].append(now)
            return True, 0
        
        # Calculate retry after (time until the oldest request expires)
        wait_time = int(self.window_seconds - (now - self.client_requests[client_ip][0]))
        return False, wait_time
