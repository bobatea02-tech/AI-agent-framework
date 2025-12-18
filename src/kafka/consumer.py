from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    from kafka import KafkaConsumer, TopicPartition  # type: ignore
    from kafka.errors import KafkaError  # type: ignore
except ImportError:
    KafkaConsumer = None
    KafkaError = None

from src.kafka.config import KafkaConfig

logger = logging.getLogger(__name__)


class WorkflowConsumer:
    """
    Kafka consumer that reads workflow submission messages and triggers 
    corresponding Airflow DAGs via the Airflow REST API.
    """

    def __init__(self) -> None:
        self.running = True
        self.consumer: Optional[KafkaConsumer] = None
        
        # Airflow Configuration
        self.airflow_url = os.getenv("AIRFLOW_URL", "http://localhost:8080/api/v1")
        self.airflow_auth = (os.getenv("AIRFLOW_USERNAME", "admin"), os.getenv("AIRFLOW_PASSWORD", "admin"))
        
        self._setup_consumer()

    def _setup_consumer(self) -> None:
        if not KafkaConsumer:
            logger.warning("kafka-python not installed. Consumer disabled.")
            return

        try:
            config = KafkaConfig.CONSUMER_CONFIG.copy()
            # Ensure manual commit is used for reliability
            config["enable_auto_commit"] = False
            config["group_id"] = os.getenv("KAFKA_GROUP_ID", "airflow_trigger_group")
            
            logger.info("Initializing KafkaConsumer for topic: %s", KafkaConfig.WORKFLOWS_TOPIC)
            self.consumer = KafkaConsumer(
                KafkaConfig.WORKFLOWS_TOPIC,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                **config
            )
            logger.info("KafkaConsumer initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize KafkaConsumer: %s", e)
            self.consumer = None

    def start_consuming(self) -> None:
        """Start the main consumption loop."""
        if not self.consumer:
            logger.error("Consumer not initialized. Exiting.")
            return

        logger.info("Starting consumption loop...")
        
        while self.running:
            try:
                # Poll for messages
                msg_pack = self.consumer.poll(timeout_ms=1000, max_records=10)

                for tp, messages in msg_pack.items():
                    for msg in messages:
                        if not self.running:
                            break
                        
                        success = self._process_message(msg.value)
                        
                        if success:
                            # Commit offset manually after successful processing
                            # We commit up to this message. 
                            # Note: commit is usually for the next offset, so msg.offset + 1
                            try:
                                from kafka import OffsetAndMetadata
                                meta = {tp: OffsetAndMetadata(msg.offset + 1, None)}
                                self.consumer.commit(meta)
                                logger.debug("Committed offset %s for partition %s", msg.offset + 1, tp.partition)
                            except Exception as e:
                                logger.error("Failed to commit offset: %s", e)
                        else:
                            # Decide strategy: skip, retry, or DLQ?
                            # For now, we log error and arguably should NOT commit to retry?
                            # But if it's a permanent error (e.g. bad payload), retrying loops forever.
                            # We'll log and commit to move forward for now, but in prod use DLQ.
                            logger.warning("Skipping message at offset %s due to processing failure", msg.offset)
                            # self.consumer.commit(...) # Skipping commit implies re-read on restart
                            
            except Exception as e:
                logger.error("Error in consumption loop: %s", e)
                time.sleep(5)

        self.close()

    def _process_message(self, payload: Dict[str, Any]) -> bool:
        """
        Process a single message: parse, map to DAG, trigger Airflow.
        Returns:
            bool: True if processed successfully (even if Airflow failed, if we handled it), 
                  False if we want to retry parsing/logic.
        """
        try:
            workflow_id = payload.get("workflow_id")
            execution_id = payload.get("execution_id")
            conf = payload.get("input", {})  # Pass input as DAG conf

            logger.info("Processing message for workflow: %s, execution: %s", workflow_id, execution_id)

            if not workflow_id or not execution_id:
                logger.error("Invalid payload: missing workflow_id or execution_id")
                return True # Treat as "processed" (bad data) to avoid poison pill loop

            dag_id = self._get_dag_id(workflow_id)
            if not dag_id:
                logger.error("No DAG mapping found for workflow_id: %s", workflow_id)
                return True # Treat as processed

            # Trigger Airflow
            return self.trigger_airflow_dag(dag_id, execution_id, conf)

        except Exception as e:
            logger.error("Unexpected error processing message: %s", e)
            return False

    def _get_dag_id(self, workflow_id: str) -> Optional[str]:
        """Map generic workflow_id to specific Airflow DAG ID."""
        # Simple mapping or DB lookup
        # For now, simplistic identity or prefix
        # Example: "document-processing" -> "document_processing_dag"
        # Or just return workflow_id if they match
        clean_id = workflow_id.replace("-", "_")
        return f"{clean_id}_dag"

    def trigger_airflow_dag(self, dag_id: str, execution_id: str, conf: Dict[str, Any]) -> bool:
        """
        Trigger a DAG run in Airflow.
        """
        if not requests:
            logger.warning("requests library not installed. Cannot call Airflow.")
            return False

        url = f"{self.airflow_url}/dags/{dag_id}/dagRuns"
        
        # Add execution_id to conf so DAG knows strictly which DB record to update
        payload_conf = conf.copy()
        payload_conf["execution_id"] = execution_id
        
        body = {
            "conf": payload_conf,
            "dag_run_id": f"s_{execution_id}_{int(time.time())}" # Unique run ID
        }

        try:
            logger.info("Triggering DAG %s for execution %s", dag_id, execution_id)
            response = requests.post(
                url, 
                json=body, 
                auth=self.airflow_auth,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Successfully triggered DAG %s. Response: %s", dag_id, response.json())
            return True
        except requests.exceptions.RequestException as e:
            logger.error("Failed to trigger Airflow DAG %s: %s", dag_id, e)
            if e.response:
                logger.error("Airflow response: %s", e.response.text)
            return False

    def shutdown(self) -> None:
        """Signal the consumer loop to stop."""
        logger.info("Shutdown signal received")
        self.running = False

    def close(self) -> None:
        """Clean up resources."""
        if self.consumer:
            logger.info("Closing Kafka consumer...")
            self.consumer.close()
            logger.info("Kafka consumer closed")


def main() -> None:
    # Setup logging to console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    consumer = WorkflowConsumer()

    def signal_handler(signum: int, frame: Any) -> None:
        consumer.shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    consumer.start_consuming()


if __name__ == "__main__":
    main()
