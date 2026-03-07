from collections.abc import Callable
from typing import Any, TypeVar
from collections import OrderedDict
from functools import wraps


Function = TypeVar('Function', bound=Callable[..., Any])


def cache(max_size: int) -> Callable[[Function], Function]:
    """
    Returns decorator, which stores result of function
    for `max_size` most recent function arguments.
    :param max_size: max amount of unique arguments to store values for
    :return: decorator, which wraps any function passed
    """
    def first_level_decorator(func: Function) -> Any:
        cache_dict: OrderedDict[Any, Any] = OrderedDict()

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if args in cache_dict.keys():
                cache_dict.move_to_end(args)
                return cache_dict[args]
            result: Any = func(*args, **kwargs)
            if len(cache_dict) == max_size:
                cache_dict.popitem(last=False)
            cache_dict[args] = result
            return result

        return wrapper

    return first_level_decorator
