# AI Agent Framework

A lightweight, modular framework for orchestrating AI workflows using Large Language Models (LLMs), tools, and custom scripts. Built with FastAPI, Redis, and a robust DAG-based task scheduler.

## Features

- **DAG-based Workflow Orchestration**: Define workflows as directed acyclic graphs (DAGs) with automatic topological sorting and dependency resolution.
- **Multi-Executor Support**: Execute tasks via LLMs (OpenAI, Ollama), HTTP tools, and custom scripts.
- **State Machine**: Track task execution state (pending, running, succeeded, failed, skipped) with automatic upstream dependency validation.
- **Structured JSON Logging**: All events logged as JSON for easy parsing and integration with observability platforms.
- **Redis State Persistence**: Save and retrieve workflow state from Redis with configurable TTLs.
- **FastAPI REST API**: Simple async HTTP endpoints for workflow submission and status tracking.
- **Flexible Input Resolution**: Placeholder-based input system for passing outputs from upstream tasks to downstream consumers.

## Quick Start

### Prerequisites

- Python 3.10+
- Redis (optional, for state persistence)
- OpenAI API key or local Ollama instance (optional, for LLM tasks)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-agent-framework.git
cd ai-agent-framework
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
export OPENAI_API_KEY="sk-..."
export REDIS_HOST="localhost"
export REDIS_PORT=6379
```

### Running the Server

```bash
python -m uvicorn src.api.routes:app --host 127.0.0.1 --port 8000
```

Then open:
- API root: http://127.0.0.1:8000/
- Health: http://127.0.0.1:8000/health
- Swagger UI: http://127.0.0.1:8000/docs

## Usage

### Example: Research Agent Workflow

```python
import requests
import json

workflow_request = {
  "workflow": {
    "name": "research_agent",
    "description": "Classify query, search web, summarize results",
    "tasks": [
      {
        "id": "classify",
        "type": "llm",
        "config": {
          "model": "gpt-4",
          "prompt": "Classify the following query into one of: factual, opinion, or creative. Query: {query}"
        },
        "inputs": {}
      },
      {
        "id": "search",
        "type": "tool",
        "config": {
          "tool": "web_request",
          "url": "https://api.example.com/search",
          "method": "GET",
          "params": {"q": "{query}"}
        },
        "inputs": {"query": "${__input__.query}"}
      },
      {
        "id": "summarize",
        "type": "llm",
        "config": {
          "model": "gpt-4",
          "prompt": "Summarize the following search results:\n{search_results}"
        },
        "inputs": {"search_results": "${search.output}"}
      }
    ],
    "edges": [
      ["classify", "search"],
      ["search", "summarize"]
    ]
  },
  "input_data": {
    "query": "Explain quantum computing for a 12-year-old"
  }
}

response = requests.post(
  "http://127.0.0.1:8000/workflows/execute",
  json=workflow_request
)

result = response.json()
print(json.dumps(result, indent=2))
```

### Response Structure

```json
{
  "status": "success",
  "output": {
    "classify": "factual",
    "search": [
      {
        "title": "Quantum Computing Explained",
        "url": "https://...",
        "snippet": "..."
      }
    ],
    "summarize": "Quantum computing uses quantum bits..."
  },
  "metrics": {
    "total_duration_ms": 2350,
    "task_durations": {
      "classify": 600,
      "search": 900,
      "summarize": 850
    },
    "task_statuses": {
      "classify": "success",
      "search": "success",
      "summarize": "success"
    }
  }
}
```

## Project Structure

```
ai-agent-framework/
├── src/
│   ├── api/
│   │   └── routes.py          # FastAPI endpoints
│   ├── core/
│   │   ├── dag.py             # DAG and TaskNode classes
│   │   ├── state_machine.py   # StateMachine for tracking task state
│   │   ├── workflow.py        # Workflow and Task definitions (optional)
│   │   └── orchestrator.py    # Orchestrator for executing workflows
│   ├── executors/
│   │   ├── base.py            # BaseExecutor abstract class
│   │   ├── llm_executor.py    # LLM executor (OpenAI/Ollama)
│   │   ├── tool_executor.py   # Tool executor (HTTP, Google Search)
│   │   └── script_executor.py # Script executor (Python)
│   ├── memory/
│   │   └── redis_store.py     # Redis state persistence
│   ├── observability/
│   │   └── logger.py          # JSON structured logging
│   └── config.py              # Configuration (Pydantic)
├── scripts/
│   └── demo_state_machine.py  # Demo script showing DAG + StateMachine
├── tests/
│   └── (unit tests TBD)
├── requirements.txt           # Python dependencies
├── .gitignore
├── .env.example              # Environment variables template
├── LICENSE
└── README.md                 # This file
```

## Core Concepts

### DAG (Directed Acyclic Graph)

Tasks are organized in a DAG where edges represent dependencies. The framework uses **Kahn's algorithm** for topological sorting to determine safe execution order.

```python
from src.core.dag import DAG, TaskNode

# Create tasks
task_a = TaskNode(id="A", type="llm")
task_b = TaskNode(id="B", type="tool")
task_c = TaskNode(id="C", type="llm")

# Build DAG
dag = DAG(
  tasks=[task_a, task_b, task_c],
  edges=[("A", "B"), ("B", "C")]
)

# Get safe execution order
order = dag.topological_sort()  # ["A", "B", "C"]

# Get parallel execution groups
groups = dag.execution_groups()  # [["A"], ["B"], ["C"]]
```

### State Machine

Tracks task state and determines which tasks are runnable (all upstream tasks succeeded).

```python
from src.core.state_machine import StateMachine, TaskState

sm = StateMachine(dag=dag)

# Check runnable tasks
runnable = sm.next_runnable()  # ["A"]

# Mark task running
sm.mark_running("A")

# Mark task succeeded with result
sm.mark_succeeded("A", result={"value": 42})

# Now B is runnable
runnable = sm.next_runnable()  # ["B"]
```

### Executors

Executors handle the actual work. Implement the `BaseExecutor` interface:

```python
from src.executors.base import BaseExecutor

class CustomExecutor(BaseExecutor):
    def execute(self, config: Dict[str, Any], inputs: Dict[str, Any]) -> Any:
        # Your custom logic here
        return result
```

## Configuration

Create a `.env` file in the project root (or use environment variables):

```
# API
API_HOST=127.0.0.1
API_PORT=8000

# LLM
OPENAI_API_KEY=sk-...
OLLAMA_HOST=http://localhost:11434

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# Database (optional)
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_dag.py -v
```

## Development

### Code Style

We use `black` for formatting and `ruff` for linting:

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

Use `mypy` for static type analysis:

```bash
mypy src/
```

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit your changes: `git commit -am 'Add feature'`.
4. Push to the branch: `git push origin feature/your-feature`.
5. Submit a pull request.

## Roadmap

- [ ] Async/await execution with background job queue
- [ ] Workflow persistence and resumption
- [ ] Conditional task execution (if/else)
- [ ] Loop/iteration support
- [ ] Multi-step LLM agents with function calling
- [ ] Caching layer for executor results
- [ ] Webhook support for external task completion
- [ ] Web UI for workflow monitoring and debugging

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/yourusername/ai-agent-framework/issues).

## Authors

- Your Name (you@example.com)

## Acknowledgments

- Inspired by Apache Airflow, LangGraph, and other DAG-based orchestration frameworks.
- Built with FastAPI, Pydantic, and Redis.
