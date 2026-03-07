from pathlib import Path
import requests
from bs4 import BeautifulSoup


# Directory to save your .json files to
# NB: create this directory if it doesn't exist
SAVED_JSON_DIR = Path(__file__).parent / 'visited_paths'


def distance(source_url: str, target_url: str) -> int | None:
    """Amount of wiki articles which should be visited to reach the target one
    starting from the source url. Assuming that the next article is choosing
    always as the very first link from the first article paragraph (tag <p>).
    If the article does not have any paragraph tags or any links in the first
    paragraph then the target is considered unreachable and None is returned.
    If the next link is pointing to the already visited article, it should be
    discarded in favor of the second link from this paragraph. And so on
    until the first not visited link will be found or no links left in paragraph.
    NB. The distance between neighbour articles (one is pointing out to the other)
    assumed to be equal to 1.
    :param source_url: the url of source article from wiki
    :param target_url: the url of target article from wiki
    :return: the distance calculated as described above
    """

    valid_titles: dict[str, bool] = {
        x.name.replace('_', ' '): True for x in (Path(__file__).parent / 'testdata').iterdir()
    }

    used: dict[str, bool] = dict()
    current_url = source_url
    dist: int = 0

    while True:

        if current_url == target_url:
            return dist

        dist += 1
        used[current_url] = True
        page = requests.get(current_url)
        soup = BeautifulSoup(page.text)
        check: bool = False

        links = soup.find('div', attrs={'class': 'mw-parser-output'}).find('p', recursive=False).find_all('a')
        for link in links:
            if (title := link.get('title')) is None or valid_titles.get(title) is None:
                continue
            next_url = 'https://ru.wikipedia.org' + link['href']
            if next_url in used:
                continue
            if not link.get('href').startswith('/wiki'):
                continue
            current_url = next_url
            check = True
            break

        if not check:
            break

    return None
