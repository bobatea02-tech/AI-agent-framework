# Quick Start Guide 🚀

## 1. Prerequisites
*   Python 3.10+
*   Docker & Docker Compose
*   Git

## 2. Installation
```bash
# Clone
git clone https://github.com/user/ai-agent-framework.git
cd ai-agent-framework

# Setup Env
cp .env.example .env
pip install -r requirements.txt

# Install Intel Tools
pip install openvino-dev opencv-python
```

## 3. Launch Services
```bash
docker compose up -d
```

## 4. Run Interactive Demo
The best way to explore is our interactive CLI:
```bash
python scripts/interactive_demo.py
```
From here you can run simulations and benchmarks.

## 5. API Usage
Submit your first workflow:
```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "X-API-Key: secret-key" \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "demo_wf", "input": {"doc": "path/to/doc.jpg"}}'
```
