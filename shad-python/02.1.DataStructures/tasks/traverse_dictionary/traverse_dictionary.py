import typing as tp
import queue


def traverse_dictionary_immutable(
        dct: tp.Mapping[str, tp.Any],
        prefix: str = "") -> list[tuple[str, int]]:
    """
    :param dct: dictionary of undefined depth with integers or other dicts as leaves with same properties
    :param prefix: prefix for key used for passing total path through recursion
    :return: list with pairs: (full key from root to leaf joined by ".", value)
    """
    if not dct:
        return []
    result: list[tuple[str, int]] = []
    for key in dct.keys():
        if isinstance(value := dct[key], int):
            result.append((prefix + '.' * (prefix != '') + key, value))
        else:
            for t in traverse_dictionary_immutable(value, prefix + '.' * (prefix != '') + key):
                result.append(t)

    return result


def traverse_dictionary_mutable(
        dct: tp.Mapping[str, tp.Any],
        result: list[tuple[str, int]],
        prefix: str = "") -> None:
    """
    :param dct: dictionary of undefined depth with integers or other dicts as leaves with same properties
    :param result: list with pairs: (full key from root to leaf joined by ".", value)
    :param prefix: prefix for key used for passing total path through recursion
    :return: None
    """
    if not dct:
        return
    for key in dct.keys():
        if isinstance(value := dct[key], int):
            result.append((prefix + '.' * (prefix != '') + key, value))
        else:
            traverse_dictionary_mutable(value, result, prefix + '.' * (prefix != '') + key)


def traverse_dictionary_iterative(
        dct: tp.Mapping[str, tp.Any]
        ) -> list[tuple[str, int]]:
    """
    :param dct: dictionary of undefined depth with integers or other dicts as leaves with same properties
    :return: list with pairs: (full key from root to leaf joined by ".", value)
    """
    result: list[tuple[str, int]] = []
    q: queue.Queue[tuple[str, dict[str, tp.Any]]] = queue.Queue()
    q.put(('', dict(dct)))

    while not q.empty():
        prefix, current_dct = q.get()
        for key in current_dct.keys():
            if isinstance(value := current_dct[key], int):
                result.append((prefix + '.' * (prefix != '') + key, value))
            else:
                q.put((prefix + '.' * (prefix != '') + key, value))

    return result
