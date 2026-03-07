import dataclasses
import dis
import io
from typing import Any, Callable
import sys

import pytest

from . import byteme


@dataclasses.dataclass
class Case:
    func: Callable[..., Any]
    expected_dis_out: str

    def __str__(self) -> str:
        return self.func.__name__


TEST_CASES = [
    Case(
        func=byteme.f0,
        expected_dis_out='''\
   0 RESUME                   0
   2 RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f1,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_CONST               1 (0)
   4 STORE_FAST               0 (a)
   6 LOAD_FAST                0 (a)
   8 RETURN_VALUE
'''
    ),
    Case(
        func=byteme.f2,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_CONST               1 (0)
   4 STORE_FAST               0 (a)
   6 LOAD_GLOBAL              1 (NULL + print)
  16 LOAD_FAST                0 (a)
  18 CALL                     1
  26 POP_TOP
  28 RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f3,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_CONST               1 (0)
   4 STORE_FAST               0 (a)
   6 LOAD_FAST                0 (a)
   8 LOAD_CONST               2 (1)
  10 BINARY_OP               13 (+=)
  14 STORE_FAST               0 (a)
  16 LOAD_GLOBAL              1 (NULL + print)
  26 LOAD_FAST                0 (a)
  28 CALL                     1
  36 POP_TOP
  38 RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f4,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_GLOBAL              1 (NULL + range)
  12 LOAD_CONST               1 (10)
  14 CALL                     1
  22 RETURN_VALUE
'''
    ),
    Case(
        func=byteme.f5,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_GLOBAL              1 (NULL + range)
  12 LOAD_CONST               1 (10)
  14 CALL                     1
  22 GET_ITER
  24 FOR_ITER                13 (to 54)
  28 STORE_FAST               0 (i)
  30 LOAD_GLOBAL              3 (NULL + print)
  40 LOAD_FAST                0 (i)
  42 CALL                     1
  50 POP_TOP
  52 JUMP_BACKWARD           15 (to 24)
  54 END_FOR
  56 RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f6,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_CONST               1 (0)
   4 STORE_FAST               0 (a)
   6 LOAD_GLOBAL              1 (NULL + range)
  16 LOAD_CONST               2 (10)
  18 CALL                     1
  26 GET_ITER
  28 FOR_ITER                 7 (to 46)
  32 STORE_FAST               1 (i)
  34 LOAD_FAST                0 (a)
  36 LOAD_CONST               3 (1)
  38 BINARY_OP               13 (+=)
  42 STORE_FAST               0 (a)
  44 JUMP_BACKWARD            9 (to 28)
  46 END_FOR
  48 LOAD_GLOBAL              3 (NULL + print)
  58 LOAD_FAST                0 (a)
  60 CALL                     1
  68 POP_TOP
  70 RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f8,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_CONST               1 ((1, 2))
   4 UNPACK_SEQUENCE          2
   8 STORE_FAST               0 (x)
  10 STORE_FAST               1 (y)
  12 RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f9,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_CONST               1 (1)
   4 LOAD_CONST               1 (1)
   6 COMPARE_OP              40 (==)
  10 POP_JUMP_IF_FALSE        2 (to 16)
  12 LOAD_CONST               1 (1)
  14 RETURN_VALUE
  16 LOAD_CONST               2 (2)
  18 RETURN_VALUE
'''
    ),
    Case(
        func=byteme.f10,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_GLOBAL              1 (NULL + range)
  12 LOAD_CONST               1 (10)
  14 CALL                     1
  22 GET_ITER
  24 FOR_ITER                 9 (to 46)
  28 STORE_FAST               0 (i)
  30 LOAD_FAST                0 (i)
  32 LOAD_CONST               2 (3)
  34 COMPARE_OP              40 (==)
  38 POP_JUMP_IF_TRUE         1 (to 42)
  40 JUMP_BACKWARD            9 (to 24)
  42 POP_TOP
  44 RETURN_CONST             0 (None)
  46 END_FOR
  48 RETURN_CONST             0 (None)
'''
    ),
    Case(
        func=byteme.f11,
        expected_dis_out='''\
   0 RESUME                   0
   2 BUILD_LIST               0
   4 LOAD_CONST               1 ((1, 2, 3))
   6 LIST_EXTEND              1
   8 STORE_FAST               0 (list_)
  10 LOAD_CONST               2 (1)
  12 LOAD_CONST               3 (2)
  14 LOAD_CONST               4 (('a', 'b'))
  16 BUILD_CONST_KEY_MAP      2
  18 STORE_FAST               1 (dict_)
  20 LOAD_FAST                0 (list_)
  22 LOAD_FAST                1 (dict_)
  24 BUILD_TUPLE              2
  26 RETURN_VALUE
'''
    ),
    Case(
        func=byteme.f12,
        expected_dis_out='''\
   0 RESUME                   0
   2 LOAD_CONST               1 (1)
   4 STORE_FAST               0 (a)
   6 LOAD_CONST               2 (2)
   8 STORE_FAST               1 (b)
  10 LOAD_CONST               3 (3)
  12 STORE_FAST               2 (c)
  14 LOAD_CONST               4 (4)
  16 STORE_FAST               3 (d)
  18 LOAD_CONST               5 (5)
  20 STORE_FAST               4 (e)
  22 LOAD_FAST                0 (a)
  24 LOAD_FAST                1 (b)
  26 LOAD_FAST                2 (c)
  28 BINARY_OP                5 (*)
  32 LOAD_FAST                3 (d)
  34 LOAD_FAST                4 (e)
  36 BINARY_OP                8 (**)
  40 BINARY_OP               11 (/)
  44 BINARY_OP                0 (+)
  48 RETURN_VALUE
'''
    ),
]


def test_version() -> None:
    """
    To do this task you need python=3.12.5
    """
    assert '3.12.5' == sys.version.split(' ', maxsplit=1)[0]


def strip_dis_out(dis_out: str) -> str:
    """Strip first 11 chars from dis_out and remove empty lines"""
    return '\n'.join(line[11:] for line in dis_out.split('\n') if line) + '\n'


@pytest.mark.parametrize('t', TEST_CASES, ids=str)
def test_byteme(t: Case) -> None:
    out = io.StringIO()
    dis.dis(t.func, file=out)
    actual_dis_out = out.getvalue()
    print(actual_dis_out)
    assert strip_dis_out(actual_dis_out) == t.expected_dis_out
