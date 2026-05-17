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
    batch_size: int = 100


@dataclass(frozen=True, slots=True)
class HttpConfig:
    timeout_seconds: int = 10


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    dsn: str = "postgresql://scrapper:scrapper@localhost:5432/scrapper"
    access_type: str = "SQL"  # "SQL" or "ORM"


@dataclass(frozen=True, slots=True)
class KafkaProducerConfig:
    bootstrap_servers: str = "localhost:9094"
    topic: str = "link-updates"


@dataclass(frozen=True, slots=True)
class ValkeyConfig:
    url: str = "redis://localhost:6379"
    ttl_seconds: int = 60


@dataclass(frozen=True, slots=True)
class RetryConfig:
    max_attempts: int = 3
    backoff_seconds: float = 1.0
    backoff_strategy: str = "constant"  # "constant" or "exponential"
    backoff_multiplier: float = 2.0
    max_backoff_seconds: float = 60.0
    retryable_status_codes: tuple[int, ...] = (500, 502, 503, 504)


@dataclass(frozen=True, slots=True)
class CircuitBreakerConfig:
    fail_max: int = 5
    reset_timeout_seconds: int = 30
    sliding_window_size: int = 10
    failure_rate_threshold: float = 50.0


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    requests_per_minute: int = 100


@dataclass(frozen=True, slots=True)
class ResilienceConfig:
    retry: RetryConfig = field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)


@dataclass(frozen=True, slots=True)
class FilteringConfig:
    stop_words: tuple[str, ...] = ()
    excluded_authors: tuple[str, ...] = ()
    min_length: int = 0


@dataclass(frozen=True, slots=True)
class SummarizationConfig:
    threshold: int = 500


@dataclass(frozen=True, slots=True)
class AiAgentKafkaConfig:
    bootstrap_servers: str = "localhost:9094"
    raw_topic: str = "link.raw-updates"
    processed_topic: str = "link.processed-updates"
    group_id: str = "ai-agent"


@dataclass(frozen=True, slots=True)
class AiAgentConfig:
    enabled: bool = False
    filtering: FilteringConfig = field(default_factory=FilteringConfig)
    summarization: SummarizationConfig = field(default_factory=SummarizationConfig)
    kafka: AiAgentKafkaConfig = field(default_factory=AiAgentKafkaConfig)


@dataclass(frozen=True, slots=True)
class NotificationConfig:
    transport: str = "http"  # "http" or "kafka"; default "kafka" set in config.toml
    kafka: KafkaProducerConfig = field(default_factory=KafkaProducerConfig)


@dataclass(frozen=True, slots=True)
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    bot_service: BotServiceConfig = field(default_factory=BotServiceConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    http: HttpConfig = field(default_factory=HttpConfig)
    database: DatabaseConfig | None = None
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    valkey: ValkeyConfig | None = None
    resilience: ResilienceConfig = field(default_factory=ResilienceConfig)
    ai_agent: AiAgentConfig = field(default_factory=AiAgentConfig)


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
    db_raw = data.get("database")

    database = None
    if db_raw is not None:
        database = DatabaseConfig(
            dsn=db_raw.get(
                "dsn", "postgresql://scrapper:scrapper@localhost:5432/scrapper"
            ),
            access_type=db_raw.get("access-type", "SQL").upper(),
        )

    notification_raw = data.get("notification", {})
    kafka_raw = notification_raw.get("kafka", {})

    resilience_raw = data.get("resilience", {})
    retry_raw = resilience_raw.get("retry", {})
    cb_raw = resilience_raw.get("circuit_breaker", {})
    rl_raw = resilience_raw.get("rate_limit", {})

    valkey_raw = data.get("valkey")
    valkey = None
    if valkey_raw is not None:
        valkey = ValkeyConfig(
            url=valkey_raw.get("url", "redis://localhost:6379"),
            ttl_seconds=int(valkey_raw.get("ttl_seconds", 60)),
        )

    ai_agent_raw = data.get("ai-agent", {})
    filtering_raw = ai_agent_raw.get("filtering", {})
    summarization_raw = ai_agent_raw.get("summarization", {})
    ai_agent_kafka_raw = ai_agent_raw.get("kafka", {})

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
            batch_size=int(scheduler.get("batch_size", 100)),
        ),
        http=HttpConfig(
            timeout_seconds=int(http.get("timeout_seconds", 10)),
        ),
        database=database,
        notification=NotificationConfig(
            transport=notification_raw.get("transport", "http"),
            kafka=KafkaProducerConfig(
                bootstrap_servers=kafka_raw.get("bootstrap_servers", "localhost:9094"),
                topic=kafka_raw.get("topic", "link.raw-updates"),
            ),
        ),
        valkey=valkey,
        resilience=ResilienceConfig(
            retry=RetryConfig(
                max_attempts=int(retry_raw.get("max_attempts", 3)),
                backoff_seconds=float(retry_raw.get("backoff_seconds", 1.0)),
                backoff_strategy=str(retry_raw.get("backoff_strategy", "constant")),
                backoff_multiplier=float(retry_raw.get("backoff_multiplier", 2.0)),
                max_backoff_seconds=float(retry_raw.get("max_backoff_seconds", 60.0)),
                retryable_status_codes=tuple(
                    retry_raw.get("retryable_status_codes", [500, 502, 503, 504])
                ),
            ),
            circuit_breaker=CircuitBreakerConfig(
                fail_max=int(cb_raw.get("fail_max", 5)),
                reset_timeout_seconds=int(cb_raw.get("reset_timeout_seconds", 30)),
                sliding_window_size=int(cb_raw.get("sliding_window_size", 10)),
                failure_rate_threshold=float(
                    cb_raw.get("failure_rate_threshold", 50.0)
                ),
            ),
            rate_limit=RateLimitConfig(
                requests_per_minute=int(rl_raw.get("requests_per_minute", 100)),
            ),
        ),
        ai_agent=AiAgentConfig(
            enabled=bool(ai_agent_raw.get("enabled", False)),
            filtering=FilteringConfig(
                stop_words=tuple(filtering_raw.get("stop-words", [])),
                excluded_authors=tuple(filtering_raw.get("excluded-authors", [])),
                min_length=int(filtering_raw.get("min-length", 0)),
            ),
            summarization=SummarizationConfig(
                threshold=int(summarization_raw.get("threshold", 500)),
            ),
            kafka=AiAgentKafkaConfig(
                bootstrap_servers=ai_agent_kafka_raw.get(
                    "bootstrap_servers", "localhost:9094"
                ),
                raw_topic=ai_agent_kafka_raw.get("raw_topic", "link.raw-updates"),
                processed_topic=ai_agent_kafka_raw.get(
                    "processed_topic", "link.processed-updates"
                ),
                group_id=ai_agent_kafka_raw.get("group_id", "ai-agent"),
            ),
        ),
    )
