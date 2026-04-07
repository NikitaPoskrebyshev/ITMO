import pytest

from scrapper.services.link_parser import (
    GitHubLink,
    InvalidLinkError,
    StackOverflowLink,
    parse_link,
)


def test_parse_github_link() -> None:
    result = parse_link("https://github.com/octocat/Hello-World")
    assert isinstance(result, GitHubLink)
    assert result.owner == "octocat"
    assert result.repo == "Hello-World"


def test_parse_github_link_with_trailing_slash() -> None:
    result = parse_link("https://github.com/octocat/Hello-World/")
    assert isinstance(result, GitHubLink)
    assert result.owner == "octocat"


def test_parse_stackoverflow_link_with_slug() -> None:
    result = parse_link("https://stackoverflow.com/questions/11227809/why-is-sorted-faster")
    assert isinstance(result, StackOverflowLink)
    assert result.question_id == 11227809


def test_parse_stackoverflow_link_without_slug() -> None:
    result = parse_link("https://stackoverflow.com/questions/11227809")
    assert isinstance(result, StackOverflowLink)
    assert result.question_id == 11227809


def test_parse_invalid_link_raises() -> None:
    with pytest.raises(InvalidLinkError):
        parse_link("https://example.com/not-supported")


def test_parse_github_without_repo_raises() -> None:
    with pytest.raises(InvalidLinkError):
        parse_link("https://github.com/octocat")


def test_parse_empty_string_raises() -> None:
    with pytest.raises(InvalidLinkError):
        parse_link("")
