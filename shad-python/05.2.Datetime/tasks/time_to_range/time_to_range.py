import datetime
import enum
import typing as tp  # noqa


class GranularityEnum(enum.Enum):
    """
    Enum for describing granularity
    """
    DAY = datetime.timedelta(days=1)
    TWELVE_HOURS = datetime.timedelta(hours=12)
    HOUR = datetime.timedelta(hours=1)
    THIRTY_MIN = datetime.timedelta(minutes=30)
    FIVE_MIN = datetime.timedelta(minutes=5)


def truncate_to_granularity(dt: datetime.datetime, gtd: GranularityEnum) -> datetime.datetime:
    """
    :param dt: datetime to truncate
    :param gtd: granularity
    :return: resulted datetime
    """
    dt.replace()
    timestamp = dt.timestamp() + 3600 * 3
    mod = gtd.value.total_seconds()
    ts = (timestamp // mod) * mod - 3600 * 3
    return datetime.datetime.fromtimestamp(ts)


class DtRange:
    def __init__(
            self,
            before: int,
            after: int,
            shift: int,
            gtd: GranularityEnum
    ) -> None:
        """
        :param before: number of datetimes should take before `given datetime`
        :param after: number of datetimes should take after `given datetime`
        :param shift: shift of `given datetime`
        :param gtd: granularity
        """
        self._before = before
        self._after = after
        self._shift = shift
        self._gtd = gtd

    def __call__(self, dt: datetime.datetime) -> list[datetime.datetime]:
        """
        :param dt: given datetime
        :return: list of datetimes in range
        """
        dt_truncated = truncate_to_granularity(dt + datetime.timedelta(hours=self._shift), self._gtd)
        result: list[datetime.datetime] = []

        for i in range(-self._before, self._after + 1):
            result.append(dt_truncated + i * self._gtd.value)

        return result


def get_interval(
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        gtd: GranularityEnum
) -> list[datetime.datetime]:
    """
    :param start_time: start of interval
    :param end_time: end of interval
    :param gtd: granularity
    :return: list of datetimes according to granularity
    """
    start = truncate_to_granularity(start_time, gtd)
    end = truncate_to_granularity(end_time, gtd)

    if start != start_time:
        start += gtd.value

    result: list[datetime.datetime] = []
    while start <= end:
        result.append(start)
        start += gtd.value
    return result
