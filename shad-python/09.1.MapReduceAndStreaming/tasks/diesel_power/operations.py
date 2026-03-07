import heapq
from abc import abstractmethod, ABC
import typing as tp
from itertools import groupby
import string
from copy import deepcopy
from collections import defaultdict
import re

TRow = dict[str, tp.Any]
TRowsIterable = tp.Iterable[TRow]
TRowsGenerator = tp.Generator[TRow, None, None]


class Operation(ABC):
    @abstractmethod
    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        pass


class Read(Operation):
    def __init__(self, filename: str, parser: tp.Callable[[str], TRow]) -> None:
        self.filename = filename
        self.parser = parser

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        with open(self.filename) as f:
            for line in f:
                yield self.parser(line)


class ReadIterFactory(Operation):
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for row in kwargs[self.name]():
            yield row


# Operations


class Mapper(ABC):
    """Base class for mappers"""
    @abstractmethod
    def __call__(self, row: TRow) -> TRowsGenerator:
        """
        :param row: one table row
        """
        pass


class Map(Operation):
    def __init__(self, mapper: Mapper) -> None:
        self.mapper = mapper

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for row in rows:
            yield from self.mapper(row)


class Reducer(ABC):
    """Base class for reducers"""
    @abstractmethod
    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        """
        :param rows: table rows
        """
        pass


class Reduce(Operation):
    def __init__(self, reducer: Reducer, keys: tp.Sequence[str]) -> None:
        self.reducer = reducer
        self.keys = keys

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        for key, groupby_items in groupby(rows, key=lambda row: [row[k] for k in self.keys]):
            yield from self.reducer(tuple(self.keys), groupby_items)


class Joiner(ABC):
    """Base class for joiners"""
    def __init__(self, suffix_a: str = '_1', suffix_b: str = '_2') -> None:
        self._a_suffix = suffix_a
        self._b_suffix = suffix_b

    @abstractmethod
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        """
        :param keys: join keys
        :param rows_a: left table rows
        :param rows_b: right table rows
        """
        pass


class Join(Operation):
    def __init__(self, joiner: Joiner, keys: tp.Sequence[str]):
        self.keys = keys
        self.joiner = joiner

    @staticmethod
    def _next(data: tp.Iterator[tp.Any]) -> tp.Any:
        try:
            return next(data)
        except StopIteration:
            return None

    def __call__(self, rows: TRowsIterable, *args: tp.Any, **kwargs: tp.Any) -> TRowsGenerator:
        data_left = groupby(rows, key=lambda row: [row[k] for k in self.keys])
        data_right = groupby(args[0], key=lambda row: [row[k] for k in self.keys])

        left_group = self._next(data_left)
        right_group = self._next(data_right)

        while left_group is not None or right_group is not None:
            if (right_group is None) or (left_group is not None and left_group[0] < right_group[0]):
                yield from self.joiner(self.keys, left_group[1], [])
                left_group = self._next(data_left)
            elif (left_group is None) or (right_group is not None and left_group[0] > right_group[0]):
                yield from self.joiner(self.keys, [], right_group[1])
                right_group = self._next(data_right)
            else:
                yield from self.joiner(self.keys, left_group[1], right_group[1])
                left_group = self._next(data_left)
                right_group = self._next(data_right)

# Dummy operators


class DummyMapper(Mapper):
    """Yield exactly the row passed"""
    def __call__(self, row: TRow) -> TRowsGenerator:
        yield row


class FirstReducer(Reducer):
    """Yield only first row from passed ones"""
    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        for row in rows:
            yield row
            break


# Mappers


class FilterPunctuation(Mapper):
    """Left only non-punctuation symbols"""
    def __init__(self, column: str):
        """
        :param column: name of column to process
        """
        self.column = column

    def __call__(self, row: TRow) -> TRowsGenerator:
        row[self.column] = row[self.column].translate(str.maketrans('', '', string.punctuation))
        yield row


class LowerCase(Mapper):
    """Replace column value with value in lower case"""
    def __init__(self, column: str):
        """
        :param column: name of column to process
        """
        self.column = column

    @staticmethod
    def _lower_case(txt: str) -> str:
        return txt.lower()

    def __call__(self, row: TRow) -> TRowsGenerator:
        row[self.column] = self._lower_case(row[self.column])
        yield row


class Split(Mapper):
    """Split row on multiple rows by separator"""
    def __init__(self, column: str, separator: str | None = None) -> None:
        """
        :param column: name of column to split
        :param separator: string to separate by
        """
        self.column = column
        self.separator = separator

    def __call__(self, row: TRow) -> TRowsGenerator:
        left_bound = 0
        txt = row.pop(self.column)
        for bound in re.finditer(self.separator if self.separator is not None else r'\s+', txt):
            new_row = deepcopy(row)
            right_bound = bound.start()
            new_row[self.column] = txt[left_bound:right_bound]
            yield new_row
            left_bound = bound.end()
        new_row = deepcopy(row)
        new_row[self.column] = txt[left_bound:]
        yield new_row


class Product(Mapper):
    """Calculates product of multiple columns"""
    def __init__(self, columns: tp.Sequence[str], result_column: str = 'product') -> None:
        """
        :param columns: column names to product
        :param result_column: column name to save product in
        """
        self.columns = columns
        self.result_column = result_column

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row = deepcopy(row)
        new_row[self.result_column] = 1
        for column in self.columns:
            new_row[self.result_column] *= row[column]
        yield new_row


class Filter(Mapper):
    """Remove records that don't satisfy some condition"""
    def __init__(self, condition: tp.Callable[[TRow], bool]) -> None:
        """
        :param condition: if condition is not true - remove record
        """
        self.condition = condition

    def __call__(self, row: TRow) -> TRowsGenerator:
        if self.condition(row):
            yield row


class Project(Mapper):
    """Leave only mentioned columns"""
    def __init__(self, columns: tp.Sequence[str]) -> None:
        """
        :param columns: names of columns
        """
        self.columns = columns

    def __call__(self, row: TRow) -> TRowsGenerator:
        new_row: TRow = dict()
        for column in self.columns:
            new_row[column] = deepcopy(row[column])
        yield new_row


# Reducers


class TopN(Reducer):
    """Calculate top N by value"""
    def __init__(self, column: str, n: int) -> None:
        """
        :param column: column name to get top by
        :param n: number of top values to extract
        """
        self.column_max = column
        self.n = n

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        yield from heapq.nlargest(self.n, rows, key=lambda row: row[self.column_max])


class TermFrequency(Reducer):
    """Calculate frequency of values in column"""
    def __init__(self, words_column: str, result_column: str = 'tf') -> None:
        """
        :param words_column: name for column with words
        :param result_column: name for result column
        """
        self.words_column = words_column
        self.result_column = result_column

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        word_count: dict[str, int] = defaultdict(int)
        rows_size: int = 0
        once: bool = True
        result_row: TRow = dict()
        for row in rows:
            rows_size += 1
            word_count[row[self.words_column]] += 1
            if once:
                once = False
                for key in group_key:
                    result_row[key] = row[key]

        for word, count in word_count.items():
            result_row[self.words_column] = word
            result_row[self.result_column] = count / rows_size
            yield deepcopy(result_row)


class Count(Reducer):
    """
    Count records by key
    Example for group_key=('a',) and column='d'
        {'a': 1, 'b': 5, 'c': 2}
        {'a': 1, 'b': 6, 'c': 1}
        =>
        {'a': 1, 'd': 2}
    """
    def __init__(self, column: str) -> None:
        """
        :param column: name for result column
        """
        self.column = column

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        rows_size: int = 0
        once: bool = True
        result_row: TRow = dict()
        for row in rows:
            rows_size += 1
            if once:
                once = False
                for key in group_key:
                    result_row[key] = row[key]
        result_row[self.column] = rows_size
        yield deepcopy(result_row)


class Sum(Reducer):
    """
    Sum values aggregated by key
    Example for key=('a',) and column='b'
        {'a': 1, 'b': 2, 'c': 4}
        {'a': 1, 'b': 3, 'c': 5}
        =>
        {'a': 1, 'b': 5}
    """
    def __init__(self, column: str) -> None:
        """
        :param column: name for sum column
        """
        self.column = column

    def __call__(self, group_key: tuple[str, ...], rows: TRowsIterable) -> TRowsGenerator:
        once: bool = True
        total_sum: int = 0
        result_row: TRow = dict()
        for row in rows:
            total_sum += row[self.column]
            if once:
                once = False
                for key in group_key:
                    result_row[key] = row[key]
        result_row[self.column] = total_sum
        yield deepcopy(result_row)


# Joiners


class InnerJoiner(Joiner):
    """Join with inner strategy"""
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        rows_b_list = list(rows_b)
        for row_a in rows_a:
            for row_b in rows_b_list:
                new_row = deepcopy(row_b)
                common_columns: set[str] = set(row_a.keys()) & set(row_b.keys()) - set(keys)
                for col in common_columns:
                    row_a[col + self._a_suffix] = row_a.pop(col)
                    new_row[col + self._b_suffix] = new_row.pop(col)
                new_row.update(row_a)
                yield new_row


class OuterJoiner(Joiner):
    """Join with outer strategy"""
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        rows_b_list = list(rows_b)
        if not rows_a:
            yield from rows_b_list
        if not rows_b_list:
            yield from rows_a
        for row_a in rows_a:
            for row_b in rows_b_list:
                row_a.update(row_b)
                yield row_a


class LeftJoiner(Joiner):
    """Join with left strategy"""
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        rows_b_list = list(rows_b)
        if not rows_b_list:
            yield from rows_a
        for row_a in rows_a:
            for row_b in rows_b_list:
                row_a.update(row_b)
                yield deepcopy(row_a)


class RightJoiner(Joiner):
    """Join with right strategy"""
    def __call__(self, keys: tp.Sequence[str], rows_a: TRowsIterable, rows_b: TRowsIterable) -> TRowsGenerator:
        rows_a_list = list(rows_a)
        if not rows_a_list:
            yield from rows_b
        for row_b in rows_b:
            for row_a in rows_a_list:
                row_b.update(row_a)
                yield deepcopy(row_b)
