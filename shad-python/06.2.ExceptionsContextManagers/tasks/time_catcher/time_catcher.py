import time
import typing as tp
from types import TracebackType


class TimeoutException(Exception):
    pass


class SoftTimeoutException(TimeoutException):
    def __str__(self) -> str:
        return 'Soft timeout exceeded!'


class HardTimeoutException(TimeoutException):
    def __str__(self) -> str:
        return 'Hard timeout exceeded!'


class TimeCatcher:

    def __init__(self, soft_timeout: float | None = None, hard_timeout: float | None = None) -> None:
        if soft_timeout is not None:
            assert 0 < soft_timeout
        if hard_timeout is not None:
            assert 0 < hard_timeout
        if hard_timeout is not None and soft_timeout is not None:
            assert soft_timeout <= hard_timeout

        self.start: float = float(time.time())
        self.soft_timeout = soft_timeout
        self.hard_timeout = hard_timeout

    def __enter__(self) -> tp.Self:
        return self

    def __exit__(self,
                 exc_type: type[TimeoutException] | None,
                 exc_val: TimeoutException | None,
                 exc_tb: TracebackType | None) -> bool | None:
        if self.hard_timeout is not None and float(self) > self.hard_timeout:
            raise HardTimeoutException
        if self.soft_timeout is not None and float(self) > self.soft_timeout:
            raise SoftTimeoutException
        if exc_val is not None:
            return True
        return None

    def __str__(self) -> str:
        return f'Time consumed: {float(self)}'

    def __float__(self) -> float:
        return float(time.time() - self.start)
