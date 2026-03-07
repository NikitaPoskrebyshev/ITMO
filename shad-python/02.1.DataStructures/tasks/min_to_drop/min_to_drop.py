import typing as tp
import collections as cl


def get_min_to_drop(seq: tp.Sequence[tp.Any]) -> int:
    """
    :param seq: sequence of elements
    :return: number of elements need to drop to leave equal elements
    """
    cnt = cl.Counter(seq)
    return 0 if len(seq) == 0 else len(seq) - max(dict(cnt).values())
