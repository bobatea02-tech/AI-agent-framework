# API Reference

The AI Agent Framework provides a RESTful API built with FastAPI.

**Base URL**: `http://localhost:8000/api/v1`

## Workflow Management

### 1. Submit a Workflow
Submit a new workflow for asynchronous execution.

*   **Endpoint**: `POST /workflows`
*   **Status Code**: `202 Accepted`

**Request Body (`WorkflowSubmission`)**:
```json
{
  "workflow_id": "string (required)",
  "input": {
    "key": "value"
  },
  "config": {
    "priority": "high"
  }
}
```

**Response (`WorkflowResponse`)**:
```json
{
  "execution_id": "uuid-string",
  "workflow_id": "string",
  "status": "queued",
  "submitted_at": "2023-10-27T10:00:00Z",
  "message": "Workflow submitted successfully"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d '{ "workflow_id": "knowledge_qa_v1", "input": {"query": "Hello"} }'
```

---

### 2. Get Workflow Status
Check the current status of an execution.

*   **Endpoint**: `GET /workflows/{execution_id}`

**Response (`WorkflowStatusResponse`)**:
```json
{
  "execution_id": "uuid-string",
  "workflow_id": "string",
  "status": "running", 
  "progress": {
    "completed_tasks": 2,
    "total_tasks": 5
  },
  "submitted_at": "2023-10-27T10:00:00Z",
  "started_at": "2023-10-27T10:00:01Z",
  "completed_at": null,
  "error": null,
  "retry_count": 0
}
```

---

### 3. Get Workflow Results
Retrieve detailed output and task history for a completed execution.

*   **Endpoint**: `GET /workflows/{execution_id}/results`

**Response (`WorkflowResults`)**:
```json
{
  "execution_id": "uuid-string",
  "workflow_id": "string",
  "status": "completed",
  "output": {
    "final_answer": "42"
  },
  "tasks": [
    {
      "task_id": "step_1",
      "task_name": "process_data",
      "status": "completed",
      "output": {...},
      "duration": 1.2,
      "retry_count": 0
    }
  ],
  "metrics": {...}
}
```

---

### 4. List Workflows
List executions with pagination.

*   **Endpoint**: `GET /workflows`
*   **Query Parameters**:
    *   `status` (optional): Filter by status (e.g., `completed`, `failed`).
    *   `limit` (default: 10): Items per page.
    *   `offset` (default: 0): Pagination offset.

**Response**: List of `WorkflowStatusResponse` objects.

---

### 5. Cancel Workflow
Stop a running workflow.

*   **Endpoint**: `DELETE /workflows/{execution_id}`
*   **Status Code**: `204 No Content`

---

## Agent Management

### 1. List Agents
Get all registered agents and their capabilities.

*   **Endpoint**: `GET /agents`

**Response (`List[AgentInfo]`)**:
```json
[
  {
    "agent_id": "form_filler_v1",
    "name": "Form Filling Agent",
    "description": "Automates government forms",
    "version": "1.0",
    "capabilities": ["ocr", "pdf_generation"]
  }
]
```

## System

### 1. Health Check
Check the health of the API and connected services (DB, Redis, Kafka).

*   **Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "services": {
    "database": "healthy",
    "kafka": "healthy",
    "redis": "healthy"
  }
}
```

## Error Codes

*   `400 Bad Request`: Invalid input or schema validation failed.
*   `404 Not Found`: Execution ID or Workflow ID does not exist.
*   `422 Unprocessable Entity`: Semantic errors in valid JSON.
*   `500 Internal Server Error`: Server-side failure (DB connection, etc.).
