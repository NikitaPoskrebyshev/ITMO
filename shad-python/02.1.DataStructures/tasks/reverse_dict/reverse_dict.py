import typing as tp


def revert(dct: tp.Mapping[str, str]) -> dict[str, list[str]]:
    """
    :param dct: dictionary to revert in format {key: value}
    :return: reverted dictionary {value: [key1, key2, key3]}
    """
    dct_reverted: dict[str, list[str]] = {}
    for key in dct.keys():
        value = dct[key]
        if dct_reverted.get(value) is None:
            dct_reverted[value] = [key]
        else:
            dct_reverted[value].append(key)

    return dct_reverted
