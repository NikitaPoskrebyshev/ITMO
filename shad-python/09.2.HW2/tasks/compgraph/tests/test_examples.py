import tempfile
import json

from click.testing import CliRunner

from examples.run_word_count import run_word_count_graph


def test_script_word_count() -> None:
    runner = CliRunner()
    input_file = tempfile.NamedTemporaryFile()
    output_file = tempfile.NamedTemporaryFile()

    docs = [
        {'doc_id': 1, 'text': 'hello, my little WORLD'},
        {'doc_id': 2, 'text': 'Hello, my little little hell'}
    ]

    expected = [
        {'text': 'hell', 'count': 1},
        {'text': 'world', 'count': 1},
        {'text': 'hello', 'count': 2},
        {'text': 'my', 'count': 2},
        {'text': 'little', 'count': 3},
    ]

    with open(input_file.name, 'w') as f:
        json.dump(docs, f)

    run_word_count_graph(input_file.name, output_file.name)

    with open(output_file.name, 'r') as f:
        while line := f.readline():
            print(line)

    # assert result.output == str(expected)


test_script_word_count()
