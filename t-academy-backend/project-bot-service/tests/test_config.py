from pathlib import Path

import pytest

from bot.config import ConfigError, load_config


def test_load_config_reads_values(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        "[telegram]\n" 'token = "secret-token"\n' "polling_timeout_seconds = 10\n",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.telegram.token == "secret-token"
    assert config.telegram.polling_timeout_seconds == 10


def test_load_config_requires_token(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("[telegram]\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(config_file)


def test_load_config_rejects_empty_token(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text('[telegram]\ntoken = "   "\n', encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(config_file)


def test_load_config_rejects_non_positive_timeout(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[telegram]\ntoken = "tok"\npolling_timeout_seconds = 0\n',
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(config_file)


def test_load_config_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path / "nonexistent.toml")
