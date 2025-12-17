FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    postgresql-client \
    tesseract-ocr \
    tesseract-ocr-hin \
    poppler-utils \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency list and install Python packages
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy application code and workflows
COPY src ./src
COPY workflows ./workflows

# Create runtime directories
RUN mkdir -p uploads logs models/openvino

# Set Python path so src is importable
ENV PYTHONPATH=/app

EXPOSE 8000

# Default command to run FastAPI with Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]


