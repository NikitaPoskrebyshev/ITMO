import typing as tp

from . import operations as ops
from . import external_sort as esrt


class Graph:
    """Computational graph implementation"""

    def __init__(self, operation: ops.Operation) -> None:
        self._operations: list[ops.Operation] = [operation]
        self._join_graphs: list['Graph'] = []

    @staticmethod
    def graph_from_iter(name: str) -> 'Graph':
        """Construct new graph which reads data from row iterator (in form of sequence of Rows
        from 'kwargs' passed to 'run' method) into graph data-flow
        Use ops.ReadIterFactory
        :param name: name of kwarg to use as data source
        """
        return Graph(ops.ReadIterFactory(name))

    @staticmethod
    def graph_from_file(filename: str, parser: tp.Callable[[str], ops.TRow]) -> 'Graph':
        """Construct new graph extended with operation for reading rows from file
        Use ops.Read
        :param filename: filename to read from
        :param parser: parser from string to Row
        """
        return Graph(ops.Read(filename, parser))

    def map(self, mapper: ops.Mapper) -> 'Graph':
        """Construct new graph extended with map operation with particular mapper
        :param mapper: mapper to use
        """
        self._operations.append(ops.Map(mapper))
        return self

    def reduce(self, reducer: ops.Reducer, keys: tp.Sequence[str]) -> 'Graph':
        """Construct new graph extended with reduce operation with particular reducer
        :param reducer: reducer to use
        :param keys: keys for grouping
        """
        self._operations.append(ops.Reduce(reducer, keys))
        return self

    def sort(self, keys: tp.Sequence[str]) -> 'Graph':
        """Construct new graph extended with sort operation
        :param keys: sorting keys (typical is tuple of strings)
        """
        self._operations.append(esrt.ExternalSort(keys))
        return self

    def join(self, joiner: ops.Joiner, join_graph: 'Graph', keys: tp.Sequence[str]) -> 'Graph':
        """Construct new graph extended with join operation with another graph
        :param joiner: join strategy to use
        :param join_graph: other graph to join with
        :param keys: keys for grouping
        """
        self._join_graphs.append(join_graph)
        self._operations.append(ops.Join(joiner, keys))
        return self

    def run(self, **kwargs: tp.Any) -> ops.TRowsIterable:
        """Single method to start execution; data sources passed as kwargs"""
        result = self._operations[0](**kwargs)
        join_graph_id = 0
        for operation in self._operations[1:]:
            if isinstance(operation, ops.Join):
                result_right = self._join_graphs[join_graph_id].run(**kwargs)
                join_graph_id += 1
                result = operation(result, result_right)
            else:
                result = operation(result)

        yield from result
