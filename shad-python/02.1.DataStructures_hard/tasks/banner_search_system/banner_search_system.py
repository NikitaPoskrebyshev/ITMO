import string
import heapq


def normalize(
        text: str
        ) -> str:
    """
    Removes punctuation and digits and convert to lower case
    :param text: text to normalize
    :return: normalized query
    """
    return ''.join(['' if x in string.punctuation + '0123456789' else x.lower() for x in text])


def get_words(
        query: str
        ) -> list[str]:
    """
    Split by words and leave only words with letters greater than 3
    :param query: query to split
    :return: filtered and split query by words
    """
    return [x for x in normalize(query).split() if len(x) > 3]


def build_index(
        banners: list[str]
        ) -> dict[str, list[int]]:
    """
    Create index from words to banners ids with preserving order and without repetitions
    :param banners: list of banners for indexation
    :return: mapping from word to banners ids
    """
    result: dict[str, list[int]] = {}
    for i in range(len(banners)):
        current_words = get_words(banners[i])
        for word in current_words:
            if result.get(word) is None:
                result[word] = [i]
            else:
                if i not in result[word]:
                    result[word].append(i)
    return result


def get_banner_indices_by_query(
        query: str,
        index: dict[str, list[int]]
        ) -> list[int]:
    """
    Extract banners indices from index, if all words from query contains in indexed banner
    :param query: query to find banners
    :param index: index to search banners
    :return: list of indices of suitable banners
    """
    if not query or not index:
        return []
    lol: list[int] = []
    heapq.heappush(lol, 1)
    heapq.heappop(lol)
    words: list[str] = get_words(query)
    result: set[int] = set()
    for word in words:
        flag = False
        for check_word in index:
            if word == check_word:
                flag = True
                if len(result):
                    result &= set(index[check_word])
                    if not len(result):
                        return []
                else:
                    result = set(index[check_word])
        if not flag:
            return []
    return list(sorted(result))


#########################
# Don't change this code
#########################

def get_banners(
        query: str,
        index: dict[str, list[int]],
        banners: list[str]
        ) -> list[str]:
    """
    Extract banners matched to queries
    :param query: query to match
    :param index: word-banner_ids index
    :param banners: list of banners
    :return: list of matched banners
    """
    indices = get_banner_indices_by_query(query, index)
    return [banners[i] for i in indices]

#########################
