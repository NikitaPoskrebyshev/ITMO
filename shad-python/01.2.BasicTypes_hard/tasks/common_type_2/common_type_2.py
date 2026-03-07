import typing as tp


def convert_to_common_type(data: list[tp.Any]) -> list[tp.Any]:
    """
    Takes list of multiple types' elements and convert each element to common type according to given rules
    :param data: list of multiple types' elements
    :return: list with elements converted to common type
    """
    types = set([type(x) for x in data])
    result: list[tp.Any] = []

    if list in types or tuple in types:
        for x in data:
            if isinstance(x, list | tuple):
                result.append(list(x))
            elif x is None or x == '':
                result.append([])
            else:
                result.append([x])
    elif bool in types:
        result = [bool(x) for x in data]
    elif float in types:
        result = [0.0 if x is None or x == '' else float(x) for x in data]
    elif int in types:
        result = [0 if x is None or x == '' else x for x in data]
    else:
        result = ["" if x is None else x for x in data]

    return result
