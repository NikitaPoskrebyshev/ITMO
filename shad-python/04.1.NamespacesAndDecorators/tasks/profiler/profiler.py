from functools import wraps
from datetime import datetime as dt


def profiler(func):  # type: ignore
    """
    Returns profiling decorator, which counts calls of function
    and measure last function execution time.
    Results are stored as function attributes: `calls`, `last_time_taken`
    :param func: function to decorate
    :return: decorator, which wraps any function passed
    """

    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore
        if wrapper.calls == wrapper.returns:
            wrapper.calls = 0
            wrapper.returns = 0
        wrapper.calls += 1
        start = dt.now()
        result = func(*args, **kwargs)
        wrapper.returns += 1
        wrapper.last_time_taken = (dt.now() - start).total_seconds()
        return result

    wrapper.calls = 0
    wrapper.returns = 0
    wrapper.last_time_taken = 0

    return wrapper
