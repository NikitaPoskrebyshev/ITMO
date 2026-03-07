import typing
import random

import pytest

from .banner_engine import (
    BannerStat, Banner, BannerStorage, EmptyBannerStorageError, EpsilonGreedyBannerEngine
)

TEST_DEFAULT_CTR = 0.1


@pytest.fixture(scope="function")
def test_banners() -> list[Banner]:
    return [
        Banner("b1", cost=1, stat=BannerStat(10, 20)),
        Banner("b2", cost=250, stat=BannerStat(20, 20)),
        Banner("b3", cost=100, stat=BannerStat(0, 20)),
        Banner("b4", cost=100, stat=BannerStat(1, 20)),
    ]


@pytest.mark.parametrize("clicks, shows, expected_ctr", [(1, 1, 1.0), (20, 100, 0.2), (5, 100, 0.05)])
def test_banner_stat_ctr_value(clicks: int, shows: int, expected_ctr: float) -> None:
    assert BannerStat(clicks, shows).compute_ctr(TEST_DEFAULT_CTR) == expected_ctr


def test_empty_stat_compute_ctr_returns_default_ctr() -> None:
    assert BannerStat(0, 0).compute_ctr(TEST_DEFAULT_CTR) == TEST_DEFAULT_CTR


def test_banner_stat_add_show_lowers_ctr() -> None:
    banner1 = BannerStat(10, 10)
    banner2 = BannerStat(10, 10)
    banner1.add_show()
    assert banner1.compute_ctr(TEST_DEFAULT_CTR) < banner2.compute_ctr(TEST_DEFAULT_CTR)


def test_banner_stat_add_click_increases_ctr() -> None:
    banner1 = BannerStat(10, 10)
    banner2 = BannerStat(10, 10)
    banner1.add_click()
    assert banner1.compute_ctr(TEST_DEFAULT_CTR) > banner2.compute_ctr(TEST_DEFAULT_CTR)


def test_get_banner_with_highest_cpc_returns_banner_with_highest_cpc(test_banners: list[Banner]) -> None:
    bs = BannerStorage(test_banners)
    highest_cpc = TEST_DEFAULT_CTR
    banner_id = ''
    for banner in test_banners:
        cpc = banner.stat.compute_ctr(TEST_DEFAULT_CTR)
        if cpc > highest_cpc:
            highest_cpc = cpc
            banner_id = banner.banner_id
    assert bs.banner_with_highest_cpc() == bs.get_banner(banner_id)


def test_banner_engine_raise_empty_storage_exception_if_constructed_with_empty_storage() -> None:
    with pytest.raises(EmptyBannerStorageError):
        EpsilonGreedyBannerEngine(BannerStorage([]), 0.0)


def test_engine_send_click_not_fails_on_unknown_banner(test_banners: list[Banner]) -> None:
    eng = EpsilonGreedyBannerEngine(BannerStorage(test_banners, TEST_DEFAULT_CTR), 0.0)
    eng.send_click("52")


def test_engine_with_zero_random_probability_shows_banner_with_highest_cpc(test_banners: list[Banner]) -> None:
    bs = BannerStorage(test_banners, TEST_DEFAULT_CTR)
    eng = EpsilonGreedyBannerEngine(bs, 0.0)
    assert eng.show_banner() == bs.banner_with_highest_cpc().banner_id


@pytest.mark.parametrize("expected_random_banner", ["b1", "b2", "b3", "b4"])
def test_engine_with_1_random_banner_probability_gets_random_banner(
        expected_random_banner: str,
        test_banners: list[Banner],
        monkeypatch: typing.Any
        ) -> None:
    monkeypatch.setattr(random, "choice", lambda x: expected_random_banner)
    bs = BannerStorage(test_banners, TEST_DEFAULT_CTR)
    eng = EpsilonGreedyBannerEngine(bs, 1.0)
    assert eng.show_banner() == expected_random_banner


def test_total_cost_equals_to_cost_of_clicked_banners(test_banners: list[Banner]) -> None:
    bs = BannerStorage(test_banners, TEST_DEFAULT_CTR)
    eng = EpsilonGreedyBannerEngine(bs, 0.0)
    check_sum = 0
    for banner in test_banners:
        check_sum += banner.cost
        eng.send_click(banner.banner_id)
    assert check_sum == eng.total_cost


def test_engine_show_increases_banner_show_stat(test_banners: list[Banner]) -> None:
    bs = BannerStorage(test_banners, TEST_DEFAULT_CTR)
    eng = EpsilonGreedyBannerEngine(bs, 0.0)
    banner = bs.banner_with_highest_cpc()
    shows = banner.stat.shows
    eng.show_banner()
    assert bs.banner_with_highest_cpc().stat.shows > shows


def test_engine_click_increases_banner_click_stat(test_banners: list[Banner]) -> None:
    bs = BannerStorage(test_banners, TEST_DEFAULT_CTR)
    eng = EpsilonGreedyBannerEngine(bs, 0.0)
    for banner in test_banners:
        clicks = banner.stat.clicks
        eng.send_click(banner.banner_id)
        assert banner.stat.clicks > clicks
