# rate_limit_handler.py - Cleaned version

import time
import random
from functools import wraps

class RateLimitHandler:
    """Rate limit handler with optimized settings."""
    
    def __init__(self, base_delay=0.5, max_delay=15.0, max_retries=3):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
    
    def retry_with_backoff(self, func):
        """Retry with exponential backoff."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = self.base_delay
            
            while retries <= self.max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    is_rate_limit = any(x in error_str for x in [
                        "quota", "rate limit", "429", "too many requests", "exceeded"
                    ])
                    
                    retries += 1
                    
                    if is_rate_limit and retries <= self.max_retries:
                        actual_delay = delay * (0.8 + random.random() * 0.4)
                        if retries == 1:
                            print(f"⏳ Rate limit - retrying...")
                        time.sleep(actual_delay)
                        delay = min(delay * 1.8, self.max_delay)
                    else:
                        raise
            
            raise Exception(f"Max retries ({self.max_retries}) exceeded")
        
        return wrapper

default_handler = RateLimitHandler(base_delay=0.5, max_delay=15.0, max_retries=3)

def retry_on_rate_limit(func):
    """Retry decorator for rate limit handling."""
    return default_handler.retry_with_backoff(func)

def sleep_with_jitter(base_seconds):
    """Sleep with minimal jitter."""
    if base_seconds <= 0:
        return 0
        
    jitter = base_seconds * 0.3 * random.random()
    sleep_time = max(0.1, base_seconds * 0.7 + jitter)
    time.sleep(sleep_time)
    return sleep_time

def batch_operations(operations, batch_size=5, delay_seconds=1.0):
    """Process operations in batches with delays."""
    for i in range(0, len(operations), batch_size):
        batch = operations[i:i+batch_size]
        yield batch
        
        if i + batch_size < len(operations):
            sleep_with_jitter(delay_seconds)