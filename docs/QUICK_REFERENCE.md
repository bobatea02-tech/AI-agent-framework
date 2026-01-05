# Quick Reference - Test Execution Guide

> **Purpose**: Fast reference for running tests and preparing demos. Print this for quick access during presentation.

---

## 🚀 Quick Start (2 Minutes)

### 1. Check Prerequisites
```powershell
python --version  # Should be 3.10+
docker --version
docker compose version
```

### 2. Start Services
```powershell
cd C:\Users\Parthi\Documents\AI-AGENT-FRAMEWORK(ANTIGRAVITY)\AI-agent-framework
docker compose up -d
timeout /t 60  # Wait for services to start
```

### 3. Verify System Health
```powershell
python scripts/health_check.py --verbose
```

**Expected**: All checks should show `[PASS]`

---

## 📊 Running Tests

### Option 1: Automated Test Suite (Recommended)
```powershell
# Run all tests with comprehensive report
python scripts/run_all_tests.py
```

### Option 2: Manual Test Execution

#### Unit Tests
```powershell
# All unit tests
pytest tests/unit -v

# Specific executor tests
pytest tests/unit/test_ocr_executor.py -v
pytest tests/unit/test_database_models.py -v

# With coverage report
pytest tests/unit -v --cov=src --cov-report=term-missing
```

**Expected Output**:
```
tests/unit/test_ocr_executor.py::test_image_execution PASSED
tests/unit/test_ocr_executor.py::test_pdf_execution PASSED
tests/unit/test_database_models.py::test_workflow_definition PASSED
...
Coverage: 72%
```

#### Verification Scripts
```powershell
# Run individual verification scripts
python tests/verify_ocr_executor.py
python tests/verify_llm_executor.py
python tests/verify_validation_executor.py
python tests/verify_models.py
python tests/verify_agents.py
```

**Expected**: Each should output SUCCESS messages

#### Integration Tests (Requires Docker Services Running)
```powershell
# Make sure Docker services are up first
docker compose ps

# Run integration tests
pytest tests/integration -v -m integration
```

#### End-to-End Tests
```powershell
pytest tests/e2e -v -m e2e
```

---

## 🎯 Quick Demo Commands

### Check System Status
```powershell
# Health check
python scripts/health_check.py

# Pre-demo checklist
python scripts/pre_demo_checklist.py

# Docker services
docker compose ps
```

### Test API
```powershell
# API health
curl http://localhost:8000/health

# List agents
curl http://localhost:8000/api/v1/agents

# API documentation
start http://localhost:8000/docs
```

### Access Airflow
```powershell
# Open Airflow UI in browser
start http://localhost:8080

# Login: admin / admin
```

### Run Interactive Demo
```powershell
python scripts/interactive_demo.py
```

---

## 🧪 Test Categories

| Test Type | Command | Purpose | Duration |
|-----------|---------|---------|----------|
| **Health Check** | `python scripts/health_check.py` | Verify all services | ~10s |
| **Unit Tests** | `pytest tests/unit -v` | Test individual components | ~30s |
| **Verification** | `python tests/verify_*.py` | Standalone component tests | ~5s each |
| **Integration** | `pytest tests/integration -v` | Test component interactions | ~1min |
| **E2E** | `pytest tests/e2e -v` | Complete workflow tests | ~2min |
| **Performance** | `pytest tests/performance -v` | Throughput and scaling | ~3min |

---

## ✅ Success Indicators

### All Tests Passing
```
✓ Health Check: SYSTEM HEALTHY
✓ Unit Tests: 35+ tests passed
✓ Verification Scripts: All SUCCESS
✓ Coverage: >70%
```

### Services Running
```powershell
docker compose ps
# All services should show "Up"
```

### API Accessible
```powershell
curl http://localhost:8000/health
# Returns: {"status":"healthy"}
```

### Airflow Accessible
- Navigate to http://localhost:8080
- Login successful
- DAGs visible in UI

---

## 🐛 Quick Troubleshooting

### Tests Failing with Import Errors
```powershell
# Set PYTHONPATH
$env:PYTHONPATH = "src"
pytest tests/unit -v
```

### Docker Services Not Starting
```powershell
# Clean restart
docker compose down -v
docker compose up -d
timeout /t 60
```

### Database Connection Failed
```powershell
# Check database is ready
docker compose logs postgres | findstr "ready"

# Restart if needed
docker compose restart postgres
```

### Kafka Timeout
```powershell
# Kafka takes longer to start (60s+)
docker compose logs kafka | findstr "started"
```

---

## 📋 Pre-Demo Checklist

Print and check before presenting:

- [ ] Python 3.10+ installed
- [ ] Docker and Docker Compose installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured
- [ ] Docker services running (`docker compose ps`)
- [ ] Health check passes (`python scripts/health_check.py`)
- [ ] Unit tests pass (`pytest tests/unit -v`)
- [ ] Verification scripts pass
- [ ] Browser tabs ready (Airflow: http://localhost:8080, API: http://localhost:8000/docs)
- [ ] Terminal ready with project directory open
- [ ] Demo guide available for reference

---

## 🎬 Demo Flow (20 minutes)

### 1. Introduction (2 min)
- Show project structure
- Explain architecture

### 2. Health Check (1 min)
```powershell
python scripts/health_check.py
```

### 3. Run Tests (3 min)
```powershell
python scripts/run_all_tests.py
# Or manually:
pytest tests/unit -v --cov=src
```

### 4. API Demo (3 min)
```powershell
# Show API docs
start http://localhost:8000/docs

# Submit workflow
curl -X POST http://localhost:8000/api/v1/workflows ...
```

### 5. Airflow Visualization (3 min)
- Open http://localhost:8080
- Show DAG graph
- Trigger workflow
- Show execution

### 6. Agent Demo (4 min)
```powershell
python tests/verify_agents.py
```

### 7. Performance (2 min)
```powershell
python scripts/benchmark_openvino.py
```

### 8. Q&A (2 min)

---

## 📝 Common Test Commands

```powershell
# Quick verification (minimal tests)
pytest tests/unit/test_ocr_executor.py tests/unit/test_database_models.py -v

# Full test suite with coverage
pytest -v --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
start htmlcov/index.html

# Run only marked tests
pytest -v -m unit          # Unit tests only
pytest -v -m integration   # Integration tests only
pytest -v -m e2e          # E2E tests only

# Run with detailed output
pytest -v -s  # -s shows print statements

# Run specific test
pytest tests/unit/test_ocr_executor.py::TestOCRExecutor::test_image_execution -v

# Stop on first failure
pytest -x

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

---

## 🎯 Expected Test Results

### verify_ocr_executor.py
```
Testing Image Execution...
Result: {'total_documents': 1, 'documents': [{'status': 'success', ...}]}

Testing PDF Execution...
Result: {'total_documents': 1, 'documents': [{'status': 'success', ...}]}

Testing Input Validation...
Testing File Not Found...

Ran 4 tests in 0.123s
OK
```

### verify_models.py
```
Testing WorkflowDefinition model...
Testing WorkflowExecution model...
Testing TaskExecution model...
Testing AgentDefinition model...

All database models verified successfully!
```

### verify_llm_executor.py
```
Testing LLM Executor initialization...
Testing single query...
Testing batch queries...

All tests passed!
```

### health_check.py
```
[PASS] Database: Connected. Found tables: workflow_definitions, ...
[PASS] Redis: Connection successful
[PASS] Kafka: Connected. Topics: 15 found.
[PASS] Airflow: Webserver accessible. Scheduler: healthy
[PASS] API: Health endpoint running
[PASS] Executors: Verified: OCRExecutor, LLMExecutor, ValidationExecutor
[PASS] FileSystem: All paths verified

SYSTEM HEALTHY
```

---

## 📚 Key Files to Show Mentor

1. **Architecture**: [docs/ARCHITECTURE.md](file:///c:/Users/Parthi/Documents/AI-AGENT-FRAMEWORK(ANTIGRAVITY)/AI-agent-framework/docs/ARCHITECTURE.md)
2. **Project Brief**: [PROJECT_BRIEF.md](file:///c:/Users/Parthi/Documents/AI-AGENT-FRAMEWORK(ANTIGRAVITY)/AI-agent-framework/PROJECT_BRIEF.md)
3. **Orchestrator**: [src/core/orchestrator.py](file:///c:/Users/Parthi/Documents/AI-AGENT-FRAMEWORK(ANTIGRAVITY)/AI-agent-framework/src/core/orchestrator.py)
4. **Executors**: [src/executors/](file:///c:/Users/Parthi/Documents/AI-AGENT-FRAMEWORK(ANTIGRAVITY)/AI-agent-framework/src/executors/)
5. **API Routes**: [src/api/routes.py](file:///c:/Users/Parthi/Documents/AI-AGENT-FRAMEWORK(ANTIGRAVITY)/AI-agent-framework/src/api/routes.py)
6. **Docker Compose**: [docker-compose.yml](file:///c:/Users/Parthi/Documents/AI-AGENT-FRAMEWORK(ANTIGRAVITY)/AI-agent-framework/docker-compose.yml)

---

## 💡 Pro Tips

> [!TIP]
> **Before Demo**: Run `python scripts/pre_demo_checklist.py` to catch issues early

> [!TIP]
> **During Demo**: Keep terminal output verbose with `-v` flag for credibility

> [!TIP]
> **Have Backup**: Take screenshots of successful test runs in case of technical issues

> [!IMPORTANT]
> **Time Management**: If pressed for time, prioritize: Health Check → Unit Tests → API Demo → Airflow

---

**Ready to impress your mentor! 🚀**
