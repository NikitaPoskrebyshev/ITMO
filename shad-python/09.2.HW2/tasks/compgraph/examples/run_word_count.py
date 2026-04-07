import click
import json

from compgraph.algorithms import word_count_graph


@click.command()
@click.argument('input_file', nargs=1)
@click.argument('output_file', nargs=1)
def run_word_count_graph(input_file: str, output_file: str) -> None:
    graph = word_count_graph(input_stream_name=input_file, text_column='text', count_column='count', from_file=True)
    result = graph.run()
    with open(output_file, 'w') as out:
        json.dump(list(result), out)


if __name__ == "__main__":
    run_word_count_graph()
