from __future__ import annotations

from dataclasses import dataclass, field


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
class PrioritizationConfig:
    high_keywords: tuple[str, ...] = ("critical", "urgent", "breaking", "security")
    low_keywords: tuple[str, ...] = ("minor", "typo", "chore", "docs")


@dataclass(frozen=True, slots=True)
class GroupingConfig:
    window_ms: int = 30000


@dataclass(frozen=True, slots=True)
class YandexGPTConfig:
    api_key: str = ""
    folder_id: str = ""
    model: str = "yandexgpt-lite/latest"


@dataclass(frozen=True, slots=True)
class AiAgentConfig:
    enabled: bool = False
    filtering: FilteringConfig = field(default_factory=FilteringConfig)
    summarization: SummarizationConfig = field(default_factory=SummarizationConfig)
    prioritization: PrioritizationConfig = field(default_factory=PrioritizationConfig)
    grouping: GroupingConfig = field(default_factory=GroupingConfig)
    kafka: AiAgentKafkaConfig = field(default_factory=AiAgentKafkaConfig)
    yandex_gpt: YandexGPTConfig | None = None
