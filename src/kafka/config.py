import os
from typing import Any, Dict

class KafkaConfig:
    BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

    PRODUCER_CONFIG: Dict[str, Any] = {
        "bootstrap_servers": BOOTSTRAP_SERVERS,
        "acks": "all",
        "retries": 3,
        "compression_type": "gzip",
        # Mapping 'max_in_flight' to kafka-python's generic param or keeping as is if wrapper handles it.
        # Assuming kafka-python usage based on previous files:
        "max_in_flight_requests_per_connection": 1,
    }

    CONSUMER_CONFIG: Dict[str, Any] = {
        "bootstrap_servers": BOOTSTRAP_SERVERS,
        "group_id": os.getenv("KAFKA_GROUP_ID", "agent_framework_group"),
        "auto_offset_reset": "earliest",
        "enable_auto_commit": False,
        "max_poll_records": 10,
        "session_timeout_ms": 30000,
    }

    WORKFLOWS_TOPIC: str = "workflows"
    RESULTS_TOPIC: str = "workflow_results"
    EVENTS_TOPIC: str = "workflow_events"
