def find_value(nums: list[int] | range, value: int) -> bool:
    """
    Find value in sorted sequence
    :param nums: sequence of integers. Could be empty
    :param value: integer to find
    :return: True if value exists, False otherwise
    """
    left, right = 0, len(nums)
    if right == 0:
        return False
    while left < right - 1:
        m = (left + right) // 2
        if value < nums[m]:
            right = m
        else:
            left = m

    return nums[left] == value
