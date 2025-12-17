from __future__ import annotations

from typing import Any, Dict, Type

from sqlalchemy.orm import Session

from .base import BaseExecutor


class DatabaseExecutor(BaseExecutor):
    """Stub executor for persisting state/results to PostgreSQL."""

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persist payload using a provided SQLAlchemy ORM model.

        config:
            model_class: ORM model class to instantiate
        inputs:
            payload: dict or ORM instance
        """
        model_cls: Type | None = config.get("model_class")
        payload = inputs.get("payload", {})

        if model_cls is None:
            raise ValueError("config.model_class is required for DatabaseExecutor")

        with self._session_factory() as session:  # type: Session
            instance = payload if hasattr(payload, "__table__") else model_cls(**payload)
            session.add(instance)
            session.commit()

        table_name = getattr(getattr(model_cls, "__table__", None), "name", None)
        return {"status": "stored", "table": table_name}


