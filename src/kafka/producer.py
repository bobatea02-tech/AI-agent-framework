from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

try:
    from kafka import KafkaProducer  # type: ignore
    from kafka.errors import KafkaError  # type: ignore
except ImportError:
    KafkaProducer = None
    KafkaError = None

from src.kafka.config import KafkaConfig

logger = logging.getLogger(__name__)


class WorkflowProducer:
    """
    Singleton Kafka producer wrapper for publishing workflow events and results.
    Handles serialization, error reporting, and graceful shutdown.
    """

    _instance: Optional[WorkflowProducer] = None

    def __new__(cls) -> WorkflowProducer:
        if cls._instance is None:
            cls._instance = super(WorkflowProducer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.producer: Optional[KafkaProducer] = None
        self._setup_producer()

    def _setup_producer(self) -> None:
        if not KafkaProducer:
            logger.warning("kafka-python not installed. Kafka functionality disabled.")
            return

        try:
            config = KafkaConfig.PRODUCER_CONFIG.copy()
            # Ensure value serializer is JSON
            config["value_serializer"] = lambda v: json.dumps(v).encode("utf-8")
            
            logger.info("Initializing KafkaProducer with servers: %s", config.get("bootstrap_servers"))
            self.producer = KafkaProducer(**config)
            logger.info("KafkaProducer initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize KafkaProducer: %s", e)
            self.producer = None

    def publish_workflow(self, workflow_id: str, execution_id: str, payload: Dict[str, Any]) -> bool:
        """
        Publish a workflow submission message.
        
        Args:
            workflow_id: ID of the workflow definition (logic grouping)
            execution_id: Unique ID of this execution (used as partition key)
            payload: Full message payload
        
        Returns:
            bool: True if published (or Kafka disabled), False on error
        """
        return self._send(
            topic=KafkaConfig.WORKFLOWS_TOPIC,
            key=execution_id, 
            value=payload
        )

    def publish_result(self, execution_id: str, result: Dict[str, Any]) -> bool:
        """
        Publish workflow results.
        
        Args:
            execution_id: Unique ID of the execution (key)
            result: Result payload
            
        Returns:
            bool: True if published, False on error
        """
        return self._send(
            topic=KafkaConfig.RESULTS_TOPIC,
            key=execution_id,
            value=result
        )

    def _send(self, topic: str, key: str, value: Dict[str, Any]) -> bool:
        if not self.producer:
            logger.warning("Kafka producer not available. Skipping message to %s (key=%s)", topic, key)
            # Return True to avoid breaking flow if optional? 
            # User requirement says "handle KafkaError exceptions specifically".
            # If strictly required, we might return False. 
            # Given previous context "optional", let's return False but log warning.
            return False

        try:
            future = self.producer.send(
                topic=topic,
                key=key.encode("utf-8"),
                value=value
            )
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            logger.info(
                "Message sent to %s [%s] offset=%s (key=%s)",
                topic,
                record_metadata.partition,
                record_metadata.offset,
                key
            )
            return True
        except KafkaError as e:
            logger.error("Kafka error sending to %s: %s", topic, e)
            return False
        except Exception as e:
            logger.error("Unexpected error sending to %s: %s", topic, e)
            return False

    def close(self) -> None:
        if self.producer:
            logger.info("Closing Kafka producer...")
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")


# Global producer instance
producer = WorkflowProducer()

# Backward compatibility if needed, or prefer using 'producer' directly
# The prompt asked for "Create global producer instance at module level"
# Previous code used default_producer(). Let's keep a factory for compatibility 
# or just expose the singleton.
def default_producer() -> WorkflowProducer:
    return producer
