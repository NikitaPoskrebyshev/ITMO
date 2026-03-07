import typing as tp


def reformat_git_log(inp: tp.IO[str], out: tp.IO[str]) -> None:
    """Reads git log from `inp` stream, reformats it and prints to `out` stream

    Expected input format: `<sha-1>\t<date>\t<author>\t<email>\t<message>`
    Output format: `<first 7 symbols of sha-1>.....<message>`
    """
    while line := inp.readline():
        text = line.split('\t')
        sha1 = text[0][:7]
        message = text[-1]
        out.write(sha1.ljust(81 - len(message), '.') + message)
