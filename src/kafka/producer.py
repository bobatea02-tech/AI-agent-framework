from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from kafka import KafkaProducer


logger = logging.getLogger(__name__)


class WorkflowProducer:
    """Kafka producer for publishing workflows to a topic."""

    def __init__(self, brokers: str = "localhost:9092", topic: str = "workflows") -> None:
        self.topic = topic
        self.client = KafkaProducer(
            bootstrap_servers=brokers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def submit(self, message: Dict[str, Any]) -> None:
        self.client.send(self.topic, message)
        self.client.flush()
        logger.info("Published workflow message to topic %s", self.topic)


def default_producer() -> WorkflowProducer:
    brokers = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    topic = os.getenv("KAFKA_WORKFLOW_TOPIC", "workflows")
    return WorkflowProducer(brokers=brokers, topic=topic)
