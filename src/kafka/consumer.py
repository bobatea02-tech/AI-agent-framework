from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from kafka import KafkaConsumer

from src.api.schemas import WorkflowRequest
from src.core.orchestrator import Orchestrator
from src.core.state_manager import StateManager
from src.core.task_flow import TaskFlow, TaskDefinition
from src.executors.api_caller_executor import APICallerExecutor
from src.executors.database_executor import DatabaseExecutor
from src.executors.llm_executor import LLMExecutor
from src.executors.ocr_executor import OCRExecutor
from src.executors.rag_executor import RAGRetrieverExecutor
from src.executors.validation_executor import ValidationExecutor


logger = logging.getLogger(__name__)


def _build_orchestrator() -> Orchestrator:
    executors: Dict[str, Any] = {
        "LLMExecutor": LLMExecutor(),
        "OCRExecutor": OCRExecutor(),
        "ValidationExecutor": ValidationExecutor(),
        "DatabaseExecutor": DatabaseExecutor(session_factory=lambda: None),
        "APICallerExecutor": APICallerExecutor(),
        "RAGRetrieverExecutor": RAGRetrieverExecutor(),
    }
    state_manager = StateManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        ttl_seconds=int(os.getenv("STATE_TTL_SECONDS", "3600")),
    )
    return Orchestrator(executors=executors, state_manager=state_manager)


class WorkflowConsumer:
    """Kafka consumer that triggers workflow execution."""

    def __init__(
        self,
        brokers: str = "localhost:9092",
        topic: str = "workflows",
        group_id: str = "agent-framework",
    ) -> None:
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=brokers,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            enable_auto_commit=True,
        )
        self.orchestrator = _build_orchestrator()

    def start(self) -> None:
        """Start consuming workflow messages and executing them."""
        logger.info("Starting Kafka workflow consumer loop")
        for msg in self.consumer:
            try:
                payload: Dict[str, Any] = msg.value
                logger.info("Received workflow message: %s", payload.get("workflow_id"))
                req = WorkflowRequest(**payload)
                flow = TaskFlow(
                    workflow_id=req.workflow_id,
                    tasks=[TaskDefinition(**t.dict()) for t in req.tasks],
                )
                self.orchestrator.execute(flow, req.input_data)
            except Exception as e:  # pragma: no cover - runtime path
                logger.error("Error handling workflow message: %s", e)


