from pathlib import Path
import subprocess


def python_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using python built-in sort
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    lst: list[tuple[int, str]] = []
    with open(file_in, 'r') as f:
        for line in f:
            a, b = line.split()
            lst.append((int(b), str(a)))
    with open(file_out, 'w') as f:
        lst.sort()
        for i in range(len(lst)):
            f.write(f'{lst[i][1]}\t{lst[i][0]}\n')


def util_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using sort util
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    subprocess.run(['sort', '-k2n', '-k1', str(file_in), '-o', str(file_out)])
