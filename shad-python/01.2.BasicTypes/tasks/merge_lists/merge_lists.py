def merge_iterative(lst_a: list[int], lst_b: list[int]) -> list[int]:
    """
    Merge two sorted lists in one sorted list
    :param lst_a: first sorted list
    :param lst_b: second sorted list
    :return: merged sorted list
    """
    a_pos, b_pos, a_len, b_len = 0, 0, len(lst_a), len(lst_b)
    result: list[int] = []
    while (a_pos < a_len) or b_pos < b_len:
        if a_pos < a_len and (b_pos >= b_len or lst_a[a_pos] < lst_b[b_pos]):
            result.append(lst_a[a_pos])
            a_pos += 1
        else:
            result.append(lst_b[b_pos])
            b_pos += 1
    return result


def merge_sorted(lst_a: list[int], lst_b: list[int]) -> list[int]:
    """
    Merge two sorted lists in one sorted list using `sorted`
    :param lst_a: first sorted list
    :param lst_b: second sorted list
    :return: merged sorted list
    """
    return list(sorted(lst_a + lst_b))
