# Development Guide 💻

This guide covers how to set up your environment for contributing to the AI Agent Framework.

## 1. Environment Setup

### Prerequisites
*   Python 3.10+
*   Docker & Docker Compose
*   Git

### Setting up Virtual Environment
```bash
# Create venv
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
```

## 2. Code Structure

*   `src/core`: Core logic (Orchestrator, StateManager).
*   `src/api`: FastAPI application (Routes, Schemas).
*   `src/executors`: Task execution logic.
*   `tests/`: Pytest suite.

## 3. Running Tests

We use `pytest` for testing.

```bash
# Run all tests
pytest tests/

# Run specific file
pytest tests/unit/test_orchestrator.py

# Run with coverage
pytest --cov=src tests/
```

## 4. Linting & Formatting

Please ensure your code is formatted before submitting a PR.
(We recommend using `black` and `ruff` - *ensure you have them installed*)

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/
```

## 5. Adding Dependencies

If you need new packages:
1.  Add them to `requirements.txt`.
2.  If they are for the Airflow worker, additionally add them to `requirements-airflow.txt`.

## 6. Release Process

1.  Update `CHANGELOG.md` with new features/fixes.
2.  Bump version in `src/__init__.py` (if applicable).
3.  Create a Pull Request.
4.  Once merged, tag the release in git:
    ```bash
    git tag -a v0.2.0 -m "Release v0.2.0"
    git push origin v0.2.0
    ```
