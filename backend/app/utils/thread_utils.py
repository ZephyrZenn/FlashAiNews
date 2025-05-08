from functools import wraps
from typing import Callable, TypeVar, Any
from concurrent.futures import Future

from app.config.thread import get_thread_pool

T = TypeVar('T')

def run_in_thread(func: Callable[..., T]) -> Callable[..., Future[T]]:
    """
    Decorator to run a function in the thread pool.
    Usage:
        @run_in_thread
        def my_function():
            # This will run in a thread
            pass
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Future[T]:
        thread_pool = get_thread_pool()
        return thread_pool.submit(func, *args, **kwargs)
    return wrapper

def submit_to_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> Future[T]:
    """
    Submit a function to the thread pool.
    Usage:
        future = submit_to_thread(my_function, arg1, arg2)
        result = future.result()  # Wait for result
    """
    thread_pool = get_thread_pool()
    return thread_pool.submit(func, *args, **kwargs) 