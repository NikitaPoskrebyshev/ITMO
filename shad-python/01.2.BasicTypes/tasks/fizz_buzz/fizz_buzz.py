def get_fizz_buzz(n: int) -> list[int | str]:
    """
    If value divided by 3 - "Fizz",
       value divided by 5 - "Buzz",
       value divided by 15 - "FizzBuzz",
    else - value.
    :param n: size of sequence
    :return: list of values.
    """
    result: list[int | str] = \
        ["Fizz" * (i % 3 == 0) + "Buzz" * (i % 5 == 0) if i % 3 == 0 or i % 5 == 0 else i for i in range(1, n + 1)]
    return result
