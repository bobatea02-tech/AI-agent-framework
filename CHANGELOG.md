# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation suite including Architecture, API Reference, and Deployment guides.
- New `TROUBLESHOOTING.md` and `DEVELOPMENT.md` guides.

## [0.1.0] - 2025-12-31

### Added
- **Core Framework**:
    - FastAPI backend with REST endpoints for workflow submission and status checking.
    - Custom Orchestrator engine for executing task DAGs.
    - `TaskFlowParser` for validating and parsing JSON/YAML workflow definitions.
    - Redis-based `StateManager` for robust execution state persistence.
- **Executors**:
    - `OCRExecutor`: Text extraction using Tesseract.
    - `LLMExecutor`: Reasoning capabilities via OpenAI/Ollama.
    - `ValidationExecutor`: Schema-based data validation.
    - `APIExecutor`: Generic HTTP request executor.
- **Infrastructure**:
    - Docker Compose setup for PostgreSQL, Redis, Kafka, Zookeeper, and Airflow.
    - `startup.sh` script for one-command bootstrapping.
- **Observability**:
    - Structured logging with `structlog`.
    - Prometheus metrics integration (`/metrics` endpoint).
- **Reference Agents**:
    - "Form Filling" agent flow.
    - "Knowledge Q&A" agent flow.

### Changed
- Refactored project structure to separate `core`, `api`, `executors`, and `tools`.
