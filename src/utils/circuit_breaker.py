
import time
import functools
from typing import Callable, Any
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(str, Enum):
    CLOSED = "CLOSED"     # Normal operation
    OPEN = "OPEN"         # Failing, short-circuit
    HALF_OPEN = "HALF_OPEN" # Testing recovery

class CircuitBreaker:
    """
    Implements the Circuit Breaker pattern to prevent cascading failures.
    """
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time = 0
    
    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        state = self.state
        
        if state == CircuitState.OPEN:
            # Fast fail
            raise Exception("Circuit is OPEN")
        
        try:
            result = func(*args, **kwargs)
            # Success in any state resets counters
            if state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._failures = 0
            return result
            
        except Exception as e:
            self._failures += 1
            self._last_failure_time = time.time()
            
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit tripped to OPEN for {func.__name__} after {self._failures} failures")
            
            raise e

def circuit_breaker(breaker: CircuitBreaker):
    """Decorator to apply circuit breaker to a function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

# Shared instances for common services
openai_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
db_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10)
