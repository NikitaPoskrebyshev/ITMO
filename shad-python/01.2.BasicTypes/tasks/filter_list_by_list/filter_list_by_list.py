def filter_list_by_list(lst_a: list[int] | range, lst_b: list[int] | range) -> list[int]:
    """
    Filter first sorted list by other sorted list
    :param lst_a: first sorted list
    :param lst_b: second sorted list
    :return: filtered sorted list
    """
    result: list[int] = []
    pos, b_len = 0, len(lst_b)

    for element in lst_a:
        while pos < b_len and lst_b[pos] < element:
            pos += 1
        if pos < b_len and lst_b[pos] == element:
            continue
        result.append(element)

    return result
