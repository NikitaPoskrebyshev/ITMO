def count_util(text: str, flags: str | None = None) -> dict[str, int]:
    """
    :param text: text to count entities
    :param flags: flags in command-like format - can be:
        * -m stands for counting characters
        * -l stands for counting lines
        * -L stands for getting length of the longest line
        * -w stands for counting words
    More than one flag can be passed at the same time, for example:
        * "-l -m"
        * "-lLw"
    Ommiting flags or passing empty string is equivalent to "-mlLw"
    :return: mapping from string keys to corresponding counter, where
    keys are selected according to the received flags:
        * "chars" - amount of characters
        * "lines" - amount of lines
        * "longest_line" - the longest line length
        * "words" - amount of words
    """
    possible_flags: list[str] = list('mlLw')
    required_flags: dict[str, bool] = {f: False for f in possible_flags}
    if flags is not None:
        required_flags = {f: f in flags for f in possible_flags}

    result: dict[str, int] = {}

    lines = text.splitlines()

    lessgoo = not flags
    for flag in required_flags.keys():
        if not (required_flags[flag] or lessgoo):
            continue
        if flag == 'm':
            result['chars'] = len(text)
        elif flag == 'l':
            result['lines'] = text.count('\n')
        elif flag == 'L':
            result['longest_line'] = max([len(x) for x in lines] + [0, 0])
        else:
            words_amount = 0
            for x in lines:
                words_amount += len(x.split())
            result['words'] = words_amount

    return result
