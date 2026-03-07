import typing as tp

T = tp.TypeVar('T', int, float)


class Pair(tp.Generic[T]):
    def __init__(self, a: T, b: T) -> None:
        self._first: T = a
        self._second: T = b

    def sum(self) -> T:
        return self._first + self._second

    def first(self) -> T:
        return self._first

    def second(self) -> T:
        return self._second

    def __iadd__(self, pair: 'Pair[T]') -> 'Pair[T]':
        first_new: T = self._first + pair.first()
        second_new: T = self._second + pair.second()
        return Pair(first_new, second_new)
