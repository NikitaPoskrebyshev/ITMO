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
class AiAgentConfig:
    enabled: bool = False
    filtering: FilteringConfig = field(default_factory=FilteringConfig)
    summarization: SummarizationConfig = field(default_factory=SummarizationConfig)
    kafka: AiAgentKafkaConfig = field(default_factory=AiAgentKafkaConfig)
