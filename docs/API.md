# API Documentation 📚

The AI Agent Framework provides a RESTful API for submitting workflows, tracking progress, and managing agents.

**Base URL**: `http://localhost:8000/api/v1`

## 🔐 Authentication
Currently, the API is open for internal use. For production deployment, it is recommended to enable API Key or OAuth2 authentication via the `AUTH_TYPE` environment variable (feature pending).

## 🚀 Endpoints

### 1. Submit Workflow
Create a new workflow execution.

- **URL**: `/workflows`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Body
| Field | Type | Required | Description |
|---|---|---|---|
| `workflow_id` | string | Yes | ID of the defined workflow (e.g. `form_filling_v1`) |
| `input` | object | Yes | Input parameters for the workflow |
| `config` | object | No | Optional configuration overrides |

#### Example Request
**cURL**
```bash
curl -X POST "http://localhost:8000/api/v1/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "knowledge_qa_v1",
    "input": {
        "query": "What is the capital of France?"
    }
  }'
```

**Python**
```python
import requests

payload = {
    "workflow_id": "knowledge_qa_v1",
    "input": {"query": "What is the capital of France?"}
}
response = requests.post("http://localhost:8000/api/v1/workflows", json=payload)
print(response.json())
```

#### Response (202 Accepted)
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "knowledge_qa_v1",
  "status": "queued",
  "submitted_at": "2023-10-27T10:00:00Z",
  "message": "Workflow submitted successfully"
}
```

---

### 2. Get Workflow Status
Check the progress of a specific execution.

- **URL**: `/workflows/{execution_id}`
- **Method**: `GET`

#### Example Request
**cURL**
```bash
curl "http://localhost:8000/api/v1/workflows/550e8400-e29b-41d4-a716-446655440000"
```

#### Response (200 OK)
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "knowledge_qa_v1",
  "status": "running",
  "progress": {
    "completed_tasks": 1,
    "total_tasks": 3
  },
  "submitted_at": "2023-10-27T10:00:00Z",
  "started_at": "2023-10-27T10:00:01Z",
  "retry_count": 0
}
```

---

### 3. Get Workflow Results
Retrieve final outputs and task details.

- **URL**: `/workflows/{execution_id}/results`
- **Method**: `GET`

#### Example Request
**cURL**
```bash
curl "http://localhost:8000/api/v1/workflows/550e8400-e29b-41d4-a716-446655440000/results"
```

#### Response (200 OK)
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_id": "knowledge_qa_v1",
  "status": "completed",
  "output": {
    "answer": "The capital of France is Paris."
  },
  "tasks": [
    {
      "task_id": "retrieve_docs",
      "task_name": "Retrieve Documents",
      "status": "completed",
      "output": { "docs": [...] },
      "duration": 1.2
    },
    {
      "task_id": "generate_answer",
      "task_name": "Generate Answer",
      "status": "completed",
      "output": { "answer": "The capital of France is Paris." },
      "duration": 2.5
    }
  ]
}
```

---

### 4. List Agents
Get available agents and their capabilities.

- **URL**: `/agents`
- **Method**: `GET`

#### Example Request
**cURL**
```bash
curl "http://localhost:8000/api/v1/agents"
```

#### Response (200 OK)
```json
[
  {
    "agent_id": "form_filling_agent",
    "name": "Form Filler Agent",
    "description": "Agent specialized in filling forms",
    "version": "1.0.0",
    "capabilities": ["pdf_reading", "text_extraction", "form_filling"]
  }
]
```

---

### 5. Health Check
Monitor system health.

- **URL**: `/health`
- **Method**: `GET`

#### Response (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2023-10-27T10:05:00Z",
  "services": {
    "database": "healthy",
    "kafka": "healthy",
    "redis": "healthy"
  }
}
```

---

## ⚠️ Error Codes

| Code | Description | Troubleshooting |
|---|---|---|
| `400` | Bad Request | Check request body format and required fields. |
| `404` | Not Found | Ensure `workflow_id` or `execution_id` is correct. |
| `422` | Validation Error | Input data does not match the schema. |
| `500` | Internal Error | Check API logs. Broker might be down. |

## 🚦 Rate Limiting
Default rate limits are set to **100 requests/minute** per IP. Limits can be configured via environment variables.

## 🪝 Webhooks (Coming Soon)
Future versions will support webhook callbacks for:
- `workflow.completed`
- `workflow.failed`
