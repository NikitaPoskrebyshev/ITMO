import typing as tp


def merge(input_streams: tp.Sequence[tp.IO[bytes]], output_stream: tp.IO[bytes]) -> None:
    """
    Merge input_streams in output_stream
    :param input_streams: list of input streams. Contains byte-strings separated by "\n". Nonempty stream ends with "\n"
    :param output_stream: output stream. Contains byte-strings separated by "\n". Nonempty stream ends with "\n"
    :return: None
    """
    result: list[int] = []
    for x in input_streams:
        result += map(int, x.read().split(b'\n')[:-1])
    result.sort()
    output_stream.write(('\n'.join(list(map(str, result))) + '\n').encode('utf-8'))
