from . import Graph, operations
from copy import deepcopy
import math
import datetime
from calendar import day_name
import json


def word_count_graph(input_stream_name: str, text_column: str = 'text', count_column: str = 'count',
                     from_file: bool = False) -> Graph:
    """Constructs graph which counts words in text_column of all rows passed"""
    graph = Graph.graph_from_file(input_stream_name, json.loads) if from_file else (
        Graph.graph_from_iter(input_stream_name))
    return graph \
        .map(operations.FilterPunctuation(text_column)) \
        .map(operations.LowerCase(text_column)) \
        .map(operations.Split(text_column)) \
        .sort([text_column]) \
        .reduce(operations.Count(count_column), [text_column]) \
        .sort(['count', text_column])


def inverted_index_graph(input_stream_name: str, doc_column: str = 'doc_id', text_column: str = 'text',
                         result_column: str = 'tf_idf', from_file: bool = False) -> Graph:
    """Constructs graph which calculates td-idf for every word/document pair"""

    def _td_idf(row: operations.TRow) -> float:
        return math.log(row['docs_count'] / row['mentioned_in_doc_count'])

    graph = Graph.graph_from_file(input_stream_name, json.loads) if from_file else (
        Graph.graph_from_iter(input_stream_name))

    split_word = deepcopy(graph) \
        .map(operations.FilterPunctuation(text_column)) \
        .map(operations.LowerCase(text_column)) \
        .map(operations.Split(text_column))

    count_docs = deepcopy(graph) \
        .reduce(operations.Count('docs_count'), [])

    count_idf = deepcopy(split_word) \
        .sort([doc_column, text_column]) \
        .reduce(operations.FirstReducer(), [doc_column, text_column]) \
        .sort([text_column]) \
        .reduce(operations.Count('mentioned_in_doc_count'), [text_column]) \
        .join(operations.InnerJoiner(), count_docs, [])

    return split_word \
        .sort([doc_column]) \
        .reduce(operations.TermFrequency(text_column), [doc_column]) \
        .sort([text_column]) \
        .join(operations.InnerJoiner(), count_idf, [text_column]) \
        .map(operations.Apply(_td_idf, result_column)) \
        .map(operations.Product(['tf', result_column], result_column)) \
        .reduce(operations.TopN(result_column, 3), [text_column]) \
        .map(operations.Project([doc_column, text_column, result_column])) \
        .sort([doc_column, text_column])


def pmi_graph(input_stream_name: str, doc_column: str = 'doc_id', text_column: str = 'text',
              result_column: str = 'pmi', from_file: bool = False) -> Graph:
    """Constructs graph which gives for every document the top 10 words ranked by pointwise mutual information"""

    def _pmi(row: operations.TRow) -> float:
        return math.log(row['tf_in_doc'] / row['tf_all'])

    graph = Graph.graph_from_file(input_stream_name, json.loads) if from_file else (
        Graph.graph_from_iter(input_stream_name))

    split_word = deepcopy(graph) \
        .map(operations.FilterPunctuation(text_column)) \
        .map(operations.LowerCase(text_column)) \
        .map(operations.Split(text_column)) \
        .sort([doc_column, text_column])

    filtered = deepcopy(split_word) \
        .reduce(operations.Count('count'), [doc_column, text_column]) \
        .map(operations.Filter(lambda x: x['count'] >= 2 and len(x[text_column]) > 4))

    graph = split_word.join(operations.InnerJoiner(), filtered, [doc_column, text_column])

    graph_sum = deepcopy(graph) \
        .reduce(operations.TermFrequency(text_column, 'tf_all'), []) \
        .sort([text_column])

    return graph \
        .reduce(operations.TermFrequency(text_column, 'tf_in_doc'), [doc_column]) \
        .sort([text_column]) \
        .join(operations.InnerJoiner(), graph_sum, [text_column]) \
        .map(operations.Apply(_pmi, result_column)) \
        .map(operations.Project([doc_column, text_column, result_column])) \
        .sort([doc_column, result_column]) \
        .reduce(operations.TopN(result_column, 10), [doc_column])


def yandex_maps_graph(input_stream_name_time: str, input_stream_name_length: str,
                      enter_time_column: str = 'enter_time', leave_time_column: str = 'leave_time',
                      edge_id_column: str = 'edge_id', start_coord_column: str = 'start', end_coord_column: str = 'end',
                      weekday_result_column: str = 'weekday', hour_result_column: str = 'hour',
                      speed_result_column: str = 'speed', from_file: bool = False) -> Graph:
    """Constructs graph which measures average speed in km/h depending on the weekday and hour"""

    def _haversine_distance(row: operations.TRow) -> float:
        radius = 6373
        point1 = row['start']
        point2 = row['end']
        longitude1, latitude1, longitude2, latitude2 = map(math.radians, [*point1, *point2])
        angle = 2 * math.asin(math.sqrt(
            math.sin((latitude2 - latitude1) / 2) ** 2 + math.cos(latitude1) * math.cos(latitude2) * math.sin(
                (longitude2 - longitude1) / 2) ** 2))
        return angle * radius

    def _to_seconds(row: operations.TRow) -> float:
        for column in 'enter_time', 'leave_time':
            row[column] = datetime.datetime.strptime(row[column], '%Y%m%dT%H%M%S.%f')
        return (row['leave_time'] - row['enter_time']).total_seconds()

    length_graph = (Graph.graph_from_file(input_stream_name_length, json.loads) if from_file else (
        Graph.graph_from_iter(input_stream_name_length))) \
        .map(operations.Apply(_haversine_distance, 'length')) \
        .sort([edge_id_column]) \
        .map(operations.Project([edge_id_column, 'length']))

    time_graph = (Graph.graph_from_file(input_stream_name_time, json.loads) if from_file else (
        Graph.graph_from_iter(input_stream_name_time))) \
        .sort([edge_id_column]) \
        .join(operations.InnerJoiner(), length_graph, [edge_id_column]) \
        .sort([enter_time_column]) \
        .map(operations.Apply(_to_seconds, 'seconds')) \
        .map(operations.Project([enter_time_column, 'seconds', 'length'])) \
        .map(operations.Apply(lambda x: day_name[x[enter_time_column].weekday()][:3], weekday_result_column)) \
        .map(operations.Apply(lambda x: x[enter_time_column].hour, hour_result_column)) \
        .sort([weekday_result_column, hour_result_column])

    graph_length_sum = deepcopy(time_graph) \
        .reduce(operations.Sum('length'), [weekday_result_column, hour_result_column])

    return time_graph.reduce(operations.Sum('seconds'), [weekday_result_column, hour_result_column]) \
        .join(operations.InnerJoiner(), graph_length_sum, [weekday_result_column, hour_result_column]) \
        .map(operations.Apply(lambda x: x['length'] / x['seconds'] * 3600, speed_result_column)) \
        .map(operations.Project([weekday_result_column, hour_result_column, speed_result_column]))
