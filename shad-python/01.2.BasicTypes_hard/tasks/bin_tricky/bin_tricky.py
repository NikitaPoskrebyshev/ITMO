from collections.abc import Sequence


def find_median(nums1: Sequence[int], nums2: Sequence[int]) -> float:
    """
    Find median of two sorted sequences. At least one of sequences should be not empty.
    :param nums1: sorted sequence of integers
    :param nums2: sorted sequence of integers
    :return: middle value if sum of sequences' lengths is odd
             average of two middle values if sum of sequences' lengths is even
    """

    if len(nums1) == 0:
        n = len(nums2)
        return float(nums2[n // 2]) if n % 2 else (nums2[n // 2] + nums2[n // 2 - 1]) / 2
    if len(nums2) == 0:
        n = len(nums1)
        return float(nums1[n // 2]) if n % 2 else (nums1[n // 2] + nums1[n // 2 - 1]) / 2

    n, m = len(nums1), len(nums2)

    if n > m:
        nums1, nums2, n, m = nums2, nums1, m, n

    left, right, median_pos = 0, n, (n + m + 1) // 2

    while left <= right:
        m1 = (left + right) // 2
        m2 = median_pos - m1

        if m1 < n and nums2[m2 - 1] > nums1[m1]:
            left = m1 + 1
        elif m1 > 0 and nums1[m1 - 1] > nums2[m2]:
            right = m1 - 1
        else:
            mx = nums2[m2 - 1] if m1 == 0 else nums1[m1 - 1]
            mx = max(nums1[m1 - 1], nums2[m2 - 1]) if m1 != 0 and m2 != 0 else mx

            if (n + m) % 2:
                return float(mx)

            mn = nums2[m2] if m1 == n else nums1[m1]
            mn = min(nums1[m1], nums2[m2]) if m1 != n and m2 != m else mn

            return (mn + mx) / 2

    assert False, "Not reachable"
