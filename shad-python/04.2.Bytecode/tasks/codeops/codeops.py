import types
import dis


def merge_dicts(dct1: dict[str, int], dct2: dict[str, int]) -> None:
    for k in dct2.keys():
        if k in dct1.keys():
            dct1[k] += dct2[k]
        else:
            dct1[k] = dct2[k]


def count_operations(source_code: types.CodeType) -> dict[str, int]:
    """Count byte code operations in given source code.

    :param source_code: the bytecode operation names to be extracted from
    :return: operation counts
    """
    result: dict[str, int] = {}
    for i in dis.get_instructions(source_code):
        result[i.opname] = result.get(i.opname, 0) + 1
        if isinstance(i.argval, types.CodeType):
            merge_dicts(result, count_operations(i.argval))

    return result
