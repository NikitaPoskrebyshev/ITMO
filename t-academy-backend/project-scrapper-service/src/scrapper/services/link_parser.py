from __future__ import annotations

import re
from dataclasses import dataclass


class InvalidLinkError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class GitHubLink:
    owner: str
    repo: str
    url: str


@dataclass(frozen=True, slots=True)
class StackOverflowLink:
    question_id: int
    url: str


_GITHUB_PATTERN = re.compile(r"^https://github\.com/([^/]+)/([^/?#]+?)(?:\.git)?/?$")
_STACKOVERFLOW_PATTERN = re.compile(
    r"^https://stackoverflow\.com/questions/(\d+)(?:/[^?#]*)?/?$"
)


def parse_link(url: str) -> GitHubLink | StackOverflowLink:
    m = _GITHUB_PATTERN.match(url)
    if m:
        return GitHubLink(owner=m.group(1), repo=m.group(2), url=url)

    m = _STACKOVERFLOW_PATTERN.match(url)
    if m:
        return StackOverflowLink(question_id=int(m.group(1)), url=url)

    raise InvalidLinkError(
        f"Unsupported link: {url}. Supported types: GitHub repos and StackOverflow questions."
    )
