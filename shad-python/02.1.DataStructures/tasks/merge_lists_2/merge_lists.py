import typing as tp


def merge(seq: tp.Sequence[tp.Sequence[int]]) -> list[int]:
    """
    :param seq: sequence of sorted sequences
    :return: merged sorted list
    """
    result: list[int] = []
    for x in seq:
        result += x
    result.sort()
    return result
