from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when the application configuration is invalid."""


@dataclass(frozen=True, slots=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass(frozen=True, slots=True)
class BotServiceConfig:
    base_url: str = "http://localhost:8081"


@dataclass(frozen=True, slots=True)
class SchedulerConfig:
    interval_seconds: int = 60


@dataclass(frozen=True, slots=True)
class HttpConfig:
    timeout_seconds: int = 10


@dataclass(frozen=True, slots=True)
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    bot_service: BotServiceConfig = field(default_factory=BotServiceConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    http: HttpConfig = field(default_factory=HttpConfig)


DEFAULT_CONFIG_PATH = Path("config.toml")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    if not path.exists():
        return AppConfig()

    with path.open("rb") as file:
        data = tomllib.load(file)

    server = data.get("server", {})
    bot_service = data.get("bot_service", {})
    scheduler = data.get("scheduler", {})
    http = data.get("http", {})

    return AppConfig(
        server=ServerConfig(
            host=server.get("host", "0.0.0.0"),
            port=int(server.get("port", 8080)),
        ),
        bot_service=BotServiceConfig(
            base_url=bot_service.get("base_url", "http://localhost:8081"),
        ),
        scheduler=SchedulerConfig(
            interval_seconds=int(scheduler.get("interval_seconds", 60)),
        ),
        http=HttpConfig(
            timeout_seconds=int(http.get("timeout_seconds", 10)),
        ),
    )
