import typing as tp
from collections.abc import Callable

T = tp.TypeVar('T', bound=complex)
S = tp.TypeVar('S', bound=complex)
A = tp.TypeVar('A', bound=complex)


def f(a: Callable[[T, S, A], float], b: T, c: S, d: A) -> float:
    return a(b, c, d)


TEST_SAMPLES = """
# SUCCESS
def g(a: float, b: float, c: complex) -> int:
    return 1

f(g, 1, 4.5, 1j)

# SUCCESS
def g(a: complex, b: complex, c: complex) -> bool:
    return True

f(g, 1, 4, True)

# ERROR
def g(a: bool, b: float, c: complex) -> int:
    return 1

f(g, 1, 4.5, 1j)

# ERROR
def g(a: int, b: int, c: complex) -> int:
    return 1

f(g, 1, 4.5, 1j)

# ERROR
def g(a: int, b: float, c: float) -> int:
    return 1

f(g, 1, 4.5, 1j)

# SUCCESS
def g(a: float, b: float, c: complex) -> float:
    return 1.0

f(g, True, True, True)

# ERROR
def g(a: float, b: float, c: complex) -> complex:
    return 1j

f(g, True, True, True)
"""
