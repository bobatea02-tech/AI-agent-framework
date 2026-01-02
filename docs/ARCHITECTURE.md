# System Architecture

## Overview

The AI Agent Framework is designed as a modular, event-driven system that enables scalable and reliable execution of complex AI workflows. It decouples the core logic into distinct components: submission (Ingress), orchestration (Airflow/Custom), execution (Executors), and state management.

## High-Level Architecture

```mermaid
graph TD
    user[User / Client App] -->|HTTP REST| ingress[Ingress API (FastAPI)]
    
    subgraph "Core Services"
        ingress -->|Publish| kafka[Apache Kafka]
        airflow[Apache Airflow] -->|Schedule| ingress
        worker[Workflow Worker] -->|Consume| kafka
        worker -->|Update| redis[(Redis State Store)]
        worker -->|Persist| pg[(PostgreSQL DB)]
    end
    
    subgraph "Execution Layer"
        worker -->|Delegate| orch[Orchestrator]
        orch -->|Execute| exec_llm[LLM Executor]
        orch -->|Execute| exec_ocr[OCR Executor]
        orch -->|Execute| exec_api[API Executor]
        orch -->|Execute| exec_db[DB Executor]
    end
    
    subgraph "External Integrations"
        exec_llm -->|API| openai[OpenAI / Ollama]
        exec_api -->|HTTP| ext_api[External Services]
    end
```

## Component Description

### 1. Ingress API (FastAPI)
- **Role**: Entry point for all interactions.
- **Responsibilities**:
    - Validates workflow submissions against schemas.
    - Queues requests to Apache Kafka.
    - Provides synchronous status and result querying.
- **Location**: `src/api/`

### 2. Message Queue (Apache Kafka)
- **Role**: Asynchronous request buffer.
- **Responsibilities**:
    - Decouples submission from execution.
    - Ensures high throughput and buffering during load spikes.
    - **Topic**: `workflows`

### 3. Orchestrator
- **Role**: Manages the lifecycle of a single workflow execution.
- **Responsibilities**:
    - Parses `TaskFlow` definitions (DAG resolution).
    - Manages task dependencies and execution order.
    - Handles retries and failure propagation.
- **Location**: `src/core/orchestrator.py`

### 4. Executors
- **Role**: specialized units of work.
- **Types**:
    - **OCR Executor**: Extracts text from images/PDFs using Tesseract.
    - **LLM Executor**: Interfaces with LLMs (OpenAI/Ollama) for reasoning.
    - **Validation Executor**: Validates data against Pydantic models.
    - **Database Executor**: Performs SQL operations.
    - **API Executor**: Makes generic HTTP requests.
- **Location**: `src/executors/`

### 5. State Management
- **Redis**: Fast, in-memory storage for active execution state (e.g., intermediate task outputs).
- **PostgreSQL**: Persistent storage for historical data (Execution logs, Audit trails).

## Data Flow

1.  **Submission**: Client submits a JSON Workflow definition to `POST /workflows`.
2.  **Queueing**: API validates request and publishes event to Kafka `workflows` topic. Status is `QUEUED`.
3.  **Consumption**: Worker consumes event, initializes `Orchestrator`. Status becomes `RUNNING`.
4.  **Execution Loop**:
    *   Orchestrator resolves next runnable tasks.
    *   Invokes corresponding `Executor` for each task.
    *   Executor returns result.
    *   Result is saved to Redis and DB.
5.  **Completion**: When all tasks complete, final output is aggregated. Status becomes `COMPLETED`.

## Database Schema

The persistent storage is managed via SQLAlchemy. Key models include:

*   **`WorkflowDefinition`**: Stores reusable templates (JSON DAGs).
*   **`WorkflowExecution`**: Tracks instances of runs.
*   **`TaskExecution`**: Tracks individual task runs within a workflow.
*   **`AgentDefinition`**: Metadata for higher-level Agent abstractions.

## Error Handling & Reliability

*   **Retries**: Tasks support configurable retry counts.
*   **Checkpointing**: State is saved after every task completion. If a worker crashes, the workflow can resume from the last checkpoint.
*   **Dead Letter Queue**: Failed messages that cannot be processed are moved to a DLQ (Kafka) for manual inspection (Planned).

## Scaling Strategy

*   **Stateless Workers**: Workers can be scaled horizontally (add more pods/containers).
*   **Partitioning**: Kafka partitions enable parallel processing of workflows.
*   **Async I/O**: Executors use async/await where possible for I/O bound tasks.
