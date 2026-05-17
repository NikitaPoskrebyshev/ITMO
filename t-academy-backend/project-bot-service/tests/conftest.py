from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="session")
def kafka_bootstrap_server() -> str:
    """Start a single Kafka container shared across the whole test session."""
    from testcontainers.kafka import KafkaContainer

    with KafkaContainer() as kafka:
        yield kafka.get_bootstrap_server()
