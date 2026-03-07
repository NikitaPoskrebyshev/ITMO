from contextlib import contextmanager
from typing import Iterator, TextIO, Type
import sys
import traceback


@contextmanager
def supresser(*types_: Type[BaseException]) -> Iterator[None]:
    try:
        yield None
    except types_:
        pass


@contextmanager
def retyper(type_from: Type[BaseException], type_to: Type[BaseException]) -> Iterator[None]:
    try:
        yield None
    except type_from:
        _, exc_val, exc_tb = sys.exc_info()
        if exc_val is not None:
            raise type_to(*exc_val.args, exc_tb)
        raise


@contextmanager
def dumper(stream: TextIO | None = None) -> Iterator[None]:
    stream = sys.stderr if stream is None else stream
    try:
        yield
    except Exception:
        exc_type, exc_val, exc_tb = sys.exc_info()
        stream.write(''.join(traceback.format_exception_only(exc_type, exc_val)))
        raise
