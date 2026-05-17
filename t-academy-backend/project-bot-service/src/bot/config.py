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
class DatabaseConfig:
    dsn: str = "postgresql://bot:bot@localhost:5432/bot"
    access_type: str = "SQL"  # "SQL" or "ORM"


@dataclass(frozen=True, slots=True)
class KafkaConsumerConfig:
    bootstrap_servers: str = "localhost:9094"
    topic: str = "link-updates"
    group_id: str = "bot-service"


@dataclass(frozen=True, slots=True)
class NotificationConfig:
    transport: str = "http"  # "http" or "kafka"; default "kafka" set in config.toml
    kafka: KafkaConsumerConfig = field(default_factory=KafkaConsumerConfig)


@dataclass(frozen=True, slots=True)
class AppConfig:
    telegram: TelegramConfig
    scrapper: ScrapperConfig = field(default_factory=ScrapperConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)


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
    server_section = raw_config.get("server", {})
    database_section = raw_config.get("database", {})

    notification_section = raw_config.get("notification", {})
    kafka_section = notification_section.get("kafka", {})

    return AppConfig(
        telegram=TelegramConfig(
            token=token,
            polling_timeout_seconds=polling_timeout_seconds,
        ),
        scrapper=ScrapperConfig(
            base_url=scrapper_section.get("base_url", "http://localhost:8080"),
            timeout_seconds=int(scrapper_section.get("timeout_seconds", 10)),
        ),
        server=ServerConfig(
            host=server_section.get("host", "0.0.0.0"),
            port=int(server_section.get("port", 8081)),
        ),
        database=DatabaseConfig(
            dsn=database_section.get("dsn", "postgresql://bot:bot@localhost:5432/bot"),
            access_type=database_section.get("access-type", "SQL").upper(),
        ),
        notification=NotificationConfig(
            transport=notification_section.get("transport", "http"),
            kafka=KafkaConsumerConfig(
                bootstrap_servers=kafka_section.get(
                    "bootstrap_servers", "localhost:9094"
                ),
                topic=kafka_section.get("topic", "link-updates"),
                group_id=kafka_section.get("group_id", "bot-service"),
            ),
        ),
    )
