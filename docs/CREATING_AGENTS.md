# Creating Custom Agents 🤖

This guide explains how to build new agents using the AI Agent Framework. An "Agent" in this context is defined by a **Workflow Definition** (DAG) and potentially custom **Executors**.

## 1. Concepts

*   **Workflow Definition**: A JSON/YAML file that describes the sequence of tasks.
*   **Executor**: A Python class that checks inputs and performs a specific action (e.g., "Summarize Text").
*   **Agent Definition**: Metadata wrapping a workflow with capabilities and versioning.

## 2. Defining a Workflow

Workflows are defined in JSON.

**Example: `workflows/my_new_agent.json`**

```json
{
  "workflow_id": "summarization_agent_v1",
  "tasks": [
    {
      "id": "read_doc",
      "executor": "OCRExecutor",
      "inputs": ["uploaded_file_path"],
      "retry": 2
    },
    {
      "id": "summarize",
      "executor": "LLMExecutor",
      "inputs": ["read_doc.output"],
      "depends_on": ["read_doc"],
      "config": {
        "model": "gpt-4",
        "prompt_template": "Summarize this: {input}"
      }
    }
  ]
}
```

### Key Fields
*   `id`: Unique identifier for the task step.
*   `executor`: Name of the executor class to run (must be registered).
*   `inputs`: List of keys to fetch from `input` or previous task outputs.
*   `depends_on`: List of task IDs that must complete before this one starts.

## 3. Creating a Custom Executor

If the built-in executors (OCR, LLM, API) aren't enough, you can create a custom one.

### Step 1: Create the Class
Create a new file `src/executors/my_custom_executor.py`:

```python
from typing import Any, Dict
from src.core.executor import BaseExecutor

class MyCustomExecutor(BaseExecutor):
    def execute(self, inputs: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Your custom logic here.
        """
        data = inputs.get("data")
        
        # Perform work
        result = f"Processed: {data}"
        
        return {"result": result}
        
    def validate(self, inputs: Dict[str, Any]) -> bool:
        """
        Optional: Validate inputs before execution.
        """
        return "data" in inputs
```

### Step 2: Register the Executor
Update `src/core/orchestrator.py` or your dependency injection container to include the new executor.

```python
# src/core/orchestrator.py
from src.executors.my_custom_executor import MyCustomExecutor

def get_orchestrator():
    executors = {
        # ... existing ...
        "MyCustomExecutor": MyCustomExecutor(),
    }
    # ...
```

## 4. Testing Your Agent

1.  **Unit Test**: Test your Executor in isolation using `pytest`.
2.  **Integration Test**: Submit a workflow using your new executor to the local API.

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -d '{
    "workflow_id": "my_custom_agent",
    "input": { "data": "test" }
  }'
```

## 5. Best Practices

*   **Idempotency**: Ensure executors can be safely retried.
*   **Small Tasks**: Break down complex logic into smaller, chainable tasks.
*   **Configurable**: Use the `config` field to pass dynamic parameters (like model names or thresholds) instead of hardcoding them.
