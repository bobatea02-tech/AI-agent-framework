# AI Agent Framework - Cursor CLI Project Prompt

## Project Overview
Build a production-ready AI Agent Framework (SDK) that orchestrates intelligent workflows with LLM reasoning, tool execution, memory management, and observability. This is NOT a simple chatbot - it's a framework that can CREATE and RUN multiple AI agents with automated task flows.

## Core Architecture Components

### 1. Ingress Layer
- **FastAPI** REST API for workflow submission
- **Apache Kafka** consumer for async queue-based processing
- Accept workflow definitions with input documents/data

### 2. Orchestration Engine
- **Apache Airflow** for DAG-based task orchestration
- Custom Python orchestrator fallback for lightweight workflows
- Features:
  - Parse task flow definitions (JSON/YAML)
  - Execute tasks in sequence/parallel
  - Handle retries, timeouts, and error recovery
  - State management and checkpointing

### 3. Task Executors
Implement modular executors for:
- **OCR Executor**: Document text extraction (Tesseract/EasyOCR)
- **LLM Reasoning Executor**: OpenAI/Ollama integration
- **Validation Executor**: Data validation and field checking
- **Database Executor**: State persistence
- **API Caller Executor**: External service integration

### 4. Tools & Actions System
Plugin architecture for:
- PDF processing (PyPDF2/pdfplumber)
- OCR capabilities (Tesseract)
- LLM calls (OpenAI API/Ollama)
- Database operations (SQLAlchemy)
- Document retrieval (RAG with FAISS/ChromaDB)
- Form generation and filling

### 5. Memory & State Management
- **Redis** for fast in-memory state
- **PostgreSQL** for persistent workflow history
- Track:
  - Intermediate task outputs
  - Decision history
  - Error logs
  - Retry attempts

### 6. Observability Layer
- Structured logging (Python logging + loguru)
- Metrics collection:
  - Task execution time
  - Success/failure rates
  - Retry counts
  - Tool usage statistics
- OpenTelemetry integration (optional)

## Technical Stack

### Backend
- **Python 3.10+**
- **FastAPI** - REST API framework
- **Apache Airflow** - Workflow orchestration
- **Apache Kafka** - Message queue
- **Celery** - Distributed task queue (alternative)
- **Redis** - Caching and state
- **PostgreSQL** - Persistent storage

### AI/ML
- **OpenAI API** / **Ollama** - LLM inference
- **Intel OpenVINO** - Model optimization
- **LangChain** - Internal tool abstractions (not exposed in SDK)
- **FAISS/ChromaDB** - Vector storage for RAG
- **Tesseract/EasyOCR** - OCR engine

### Utilities
- **Pydantic** - Data validation
- **SQLAlchemy** - ORM
- **Celery** - Task queue
- **pytest** - Testing
- **Docker** - Containerization

## Project Structure

```
ai-agent-framework/
├── src/
│   ├── core/
│   │   ├── orchestrator.py          # Main orchestration engine
│   │   ├── executor.py               # Base executor class
│   │   ├── task_flow.py              # Task flow parser
│   │   └── state_manager.py          # State management
│   ├── executors/
│   │   ├── ocr_executor.py
│   │   ├── llm_executor.py
│   │   ├── validation_executor.py
│   │   └── database_executor.py
│   ├── tools/
│   │   ├── pdf_reader.py
│   │   ├── ocr_tool.py
│   │   ├── llm_client.py
│   │   └── rag_retriever.py
│   ├── agents/
│   │   ├── form_filling_agent.py     # Reference Agent 1
│   │   └── knowledge_qa_agent.py     # Reference Agent 2
│   ├── api/
│   │   ├── routes.py                 # FastAPI routes
│   │   └── schemas.py                # Pydantic models
│   ├── kafka/
│   │   ├── consumer.py
│   │   └── producer.py
│   ├── airflow/
│   │   └── dags/
│   │       └── agent_workflows.py
│   └── utils/
│       ├── logger.py
│       └── metrics.py
├── workflows/
│   ├── form_filling_flow.json        # Task flow definitions
│   └── knowledge_qa_flow.json
├── tests/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Reference Agents to Implement

### Agent 1: AI-Powered Form Filling Assistant
**Purpose**: Automate government form filling using Aadhaar/PAN documents

**Task Flow**:
1. Accept document uploads (PDF/Image)
2. OCR text extraction
3. Field extraction (Name, DOB, ID numbers)
4. Data validation
5. Auto-fill form template
6. Generate confirmation PDF

**Key Features**:
- Multi-document processing
- Field mapping intelligence
- Validation rules engine
- Form template system

### Agent 2: Knowledge Q&A Agent
**Purpose**: Answer questions with grounded citations from document corpus

**Task Flow**:
1. Accept user query
2. Retrieve relevant documents (RAG)
3. LLM reasoning with context
4. Generate answer with citations
5. Confidence scoring

**Key Features**:
- 85%+ grounded answers
- Source attribution
- Confidence metrics
- Multi-document synthesis

## Intel Optimization Requirements

### OpenVINO Integration
- Convert OCR models to OpenVINO IR format
- Optimize LLM inference (if self-hosted)
- Benchmark latency improvements
- Target: ≤3-5 seconds per workflow

### Deliverables
- Before/after performance metrics
- Model optimization scripts
- Intel DevCloud deployment guide

## Implementation Priorities

### Phase 1: Core Framework (Days 1-2)
- [ ] FastAPI skeleton with basic routes
- [ ] Orchestrator base class
- [ ] Task flow JSON schema and parser
- [ ] Basic state management with Redis

### Phase 2: Executors & Tools (Days 3-4)
- [ ] OCR executor with Tesseract
- [ ] LLM executor with OpenAI/Ollama
- [ ] Database executor with PostgreSQL
- [ ] PDF processing tool
- [ ] Memory/state persistence

### Phase 3: Apache Integration (Day 4-5)
- [ ] Kafka producer/consumer setup
- [ ] Airflow DAG definitions
- [ ] Celery task queue (alternative)
- [ ] Queue-based workflow triggering

### Phase 4: Reference Agents (Days 5-6)
- [ ] Form filling agent implementation
- [ ] Knowledge Q&A agent with RAG
- [ ] Agent configuration files
- [ ] Testing workflows

### Phase 5: Observability (Day 7)
- [ ] Structured logging
- [ ] Performance metrics collection
- [ ] Retry and error handling
- [ ] Monitoring dashboard (basic)

### Phase 6: Intel Optimization (Days 8-9)
- [ ] OpenVINO model conversion
- [ ] Benchmark suite
- [ ] Performance comparison reports

### Phase 7: Polish & Documentation (Day 10)
- [ ] Architecture diagrams
- [ ] SDK usage documentation
- [ ] API documentation (Swagger)
- [ ] Deployment guide

## Key Configuration Files

### Task Flow Definition (JSON)
```json
{
  "workflow_id": "form_filling_v1",
  "tasks": [
    {
      "id": "extract_text",
      "executor": "OCRExecutor",
      "inputs": ["uploaded_docs"],
      "retry": 3,
      "timeout": 30
    },
    {
      "id": "validate_fields",
      "executor": "ValidationExecutor",
      "inputs": ["extract_text.output"],
      "depends_on": ["extract_text"]
    }
  ]
}
```

### Docker Compose Services
- FastAPI backend
- PostgreSQL database
- Redis cache
- Kafka + Zookeeper
- Airflow (webserver, scheduler, worker)

## Non-Functional Requirements

### Performance 
- Workflow latency: ≤5 seconds per task
- Concurrent workflows: Support 10+ simultaneous
- State persistence: All intermediate outputs saved

### Reliability
- Automatic retry with exponential backoff
- Graceful degradation on tool failures
- State checkpointing for recovery

### Scalability
- Horizontal scaling via Celery workers
- Kafka for async processing
- Stateless API design

## Development Guidelines

1. **Use Pydantic** for all data models and validation
2. **Type hints** throughout the codebase
3. **Dependency injection** for executors and tools
4. **Factory pattern** for tool instantiation
5. **Strategy pattern** for different orchestration modes
6. **Async/await** where applicable (FastAPI, Kafka)

## Testing Strategy
- Unit tests for each executor
- Integration tests for task flows
- End-to-end tests for reference agents
- Performance benchmarks
- pytest with >70% coverage goal

## Deliverables Checklist
- [ ] Working web application with API
- [ ] Agent framework SDK with documentation
- [ ] Two reference agents (form filling + Q&A)
- [ ] Architecture design document
- [ ] Performance benchmarks
- [ ] Intel OpenVINO optimization proof
- [ ] Docker deployment setup
- [ ] GitHub repository with README

## Success Metrics
- Framework can execute custom workflows from JSON
- Both reference agents working end-to-end
- Intel optimization shows measurable improvement
- Clear SDK documentation for building new agents
- Observable logs and metrics for all workflows

---

**Start with**: Core orchestrator + FastAPI skeleton + task flow parser
**Then add**: Executors → Tools → Kafka → Airflow → Agents → Intel optimization
**Goal**: Production-ready framework, not just a prototype