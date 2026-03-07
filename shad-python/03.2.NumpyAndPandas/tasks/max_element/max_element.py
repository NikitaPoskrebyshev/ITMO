import numpy as np
import numpy.typing as npt


def max_element(array: npt.NDArray[np.int_]) -> int | None:
    """
    Return max element before zero for input array.
    If appropriate elements are absent, then return None
    :param array: array,
    :return: max element value or None
    """
    zeros = np.where(array == 0)[0]
    zeros += 1

    if not zeros.size:
        return None
    if zeros[-1] == array.size:
        zeros = zeros[:-1]

    return array[zeros].max() if zeros.size else None
