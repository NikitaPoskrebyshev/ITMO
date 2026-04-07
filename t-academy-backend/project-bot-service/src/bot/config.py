from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


class ConfigError(RuntimeError):
    """Raised when the application configuration is invalid."""


@dataclass(frozen=True, slots=True)
class TelegramConfig:
    token: str
    polling_timeout_seconds: int = 30


@dataclass(frozen=True, slots=True)
class ScrapperConfig:
    base_url: str = "http://localhost:8080"
    timeout_seconds: int = 10


@dataclass(frozen=True, slots=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8081


@dataclass(frozen=True, slots=True)
class AppConfig:
    telegram: TelegramConfig
    scrapper: ScrapperConfig = field(default_factory=ScrapperConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


DEFAULT_CONFIG_PATH = Path("config.toml")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    if not path.exists():
        raise ConfigError(
            "Configuration file config.toml was not found. "
            "Create it from config.example.toml and set Telegram token."
        )

    with path.open("rb") as file:
        raw_config = tomllib.load(file)

    telegram_section = raw_config.get("telegram")
    if not isinstance(telegram_section, dict):
        raise ConfigError("Section [telegram] is missing in config.toml")

    token = telegram_section.get("token")
    if not isinstance(token, str) or not token.strip():
        raise ConfigError("telegram.token must be a non-empty string")

    polling_timeout_seconds = telegram_section.get("polling_timeout_seconds", 30)
    if not isinstance(polling_timeout_seconds, int) or polling_timeout_seconds <= 0:
        raise ConfigError("telegram.polling_timeout_seconds must be a positive integer")

    scrapper_section = raw_config.get("scrapper", {})
    scrapper_base_url = scrapper_section.get("base_url", "http://localhost:8080")
    scrapper_timeout = scrapper_section.get("timeout_seconds", 10)

    server_section = raw_config.get("server", {})
    server_host = server_section.get("host", "0.0.0.0")
    server_port = server_section.get("port", 8081)

    return AppConfig(
        telegram=TelegramConfig(
            token=token,
            polling_timeout_seconds=polling_timeout_seconds,
        ),
        scrapper=ScrapperConfig(
            base_url=scrapper_base_url,
            timeout_seconds=scrapper_timeout,
        ),
        server=ServerConfig(
            host=server_host,
            port=server_port,
        ),
    )
