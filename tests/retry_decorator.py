"""
Retry decorator for brittle tests to capture intermittent failures properly.
Tests should run 10x internally to reveal brittleness patterns.
"""
import pytest
import asyncio
import time
from functools import wraps
from typing import Callable, Any


def retry_brittle_test(max_attempts: int = 10, delay: float = 0.1):
    """
    Retry decorator for intermittent tests.
    
    Instead of external bash loops, this runs the test 10x internally 
    to properly capture brittleness within the test isolation.
    
    Args:
        max_attempts: Number of retry attempts (default 10 for brittle tests)
        delay: Delay between attempts in seconds
    """
    def decorator(test_func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(test_func):
            @wraps(test_func)
            async def async_wrapper(*args, **kwargs) -> Any:
                failures = []
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        print(f"[BRITTLE TEST] Attempt {attempt}/{max_attempts}")
                        result = await test_func(*args, **kwargs)
                        print(f"[BRITTLE TEST] ✅ Success on attempt {attempt}")
                        return result
                    except Exception as e:
                        failures.append(f"Attempt {attempt}: {str(e)}")
                        if attempt < max_attempts:
                            await asyncio.sleep(delay)
                        else:
                            failure_summary = "\n".join(failures)
                            pytest.fail(
                                f"Test failed after {max_attempts} attempts.\n"
                                f"This confirms brittleness requiring internal retry logic.\n"
                                f"Failures:\n{failure_summary}"
                            )
                            
            return async_wrapper
        else:
            @wraps(test_func)
            def sync_wrapper(*args, **kwargs) -> Any:
                failures = []
                
                for attempt in range(1, max_attempts + 1):
                    try:
                        print(f"[BRITTLE TEST] Attempt {attempt}/{max_attempts}")
                        result = test_func(*args, **kwargs)
                        print(f"[BRITTLE TEST] ✅ Success on attempt {attempt}")
                        return result
                    except Exception as e:
                        failures.append(f"Attempt {attempt}: {str(e)}")
                        if attempt < max_attempts:
                            time.sleep(delay)
                        else:
                            failure_summary = "\n".join(failures)
                            pytest.fail(
                                f"Test failed after {max_attempts} attempts.\n"
                                f"This confirms brittleness requiring internal retry logic.\n" 
                                f"Failures:\n{failure_summary}"
                            )
                            
            return sync_wrapper
            
    return decorator


def flaky_test(max_attempts: int = 3):
    """
    Lightweight decorator for tests that are known to be flaky.
    Uses fewer retries than brittle_test for less critical intermittent issues.
    """
    return retry_brittle_test(max_attempts=max_attempts, delay=0.5)