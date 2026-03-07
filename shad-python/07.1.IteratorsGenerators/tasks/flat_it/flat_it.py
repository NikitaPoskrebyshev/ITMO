from collections.abc import Iterable, Iterator
from typing import Any


def flat_it(sequence: Iterable[Any]) -> Iterator[Any]:
    """
    :param sequence: iterable with arbitrary level of nested iterables
    :return: generator producing flatten sequence
    """
    for v in sequence:
        if isinstance(v, Iterable) and not (isinstance(v, str) and len(v) == 1):
            yield from flat_it(v)
        else:
            yield v
