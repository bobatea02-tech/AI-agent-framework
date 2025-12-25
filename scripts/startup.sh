#!/bin/bash

# scripts/startup.sh
# Startup script for AI Agent Framework
# Handles environment setup, service orchestration, and initialization.

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# 1. Environment Checks
log_info "Checking environment..."

if [ ! -f .env ]; then
    log_warn ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        log_info "Created .env"
    else
        log_error ".env.example not found! Cannot create .env."
        exit 1
    fi
fi

# 2. Key Generation
# Generate Airflow Fernet Key if missing
if ! grep -q "AIRFLOW__CORE__FERNET_KEY" .env; then
    log_info "Generating Airflow Fernet Key..."
    # Attempt to use python for generation, fallback to openssl
    if command -v python3 &> /dev/null; then
        FERNET_KEY=$(python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())")
    else
        FERNET_KEY=$(openssl rand -base64 32)
    fi
    
    # Append to .env
    echo "" >> .env
    echo "# Generated Keys" >> .env
    echo "AIRFLOW__CORE__FERNET_KEY=$FERNET_KEY" >> .env
    log_info "Added AIRFLOW__CORE__FERNET_KEY to .env"
fi

# Add AIRFLOW_UID if missing (required for Linux/WSL)
if ! grep -q "AIRFLOW_UID" .env; then
    if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "Adding AIRFLOW_UID to .env..."
        echo "AIRFLOW_UID=$(id -u)" >> .env
    fi
fi

# 3. Create Directories
log_info "Creating required directories..."
mkdir -p uploads logs models/openvino
mkdir -p dags plugins # For Airflow volumes

# 4. Check Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH."
    exit 1
fi

log_info "Docker environment detected."

# 5. Start Services
log_info "Starting infrastructure services (Postgres, Redis, Zookeeper)..."
docker compose up -d postgres redis zookeeper

wait_for_healthy() {
    local service=$1
    local max_retries=30
    local count=0
    
    echo -n "Waiting for $service to be healthy..."
    
    while [ $count -lt $max_retries ]; do
        # Check if service has healthcheck
        if docker inspect --format '{{.State.Health}}' "$(docker compose ps -q $service)" 2>/dev/null | grep -q "Status"; then
             status=$(docker inspect --format '{{.State.Health.Status}}' "$(docker compose ps -q $service)")
             if [ "$status" == "healthy" ]; then
                 echo -e " ${GREEN}OK${NC}"
                 return 0
             fi
        else
            # No healthcheck, just check if running
            state=$(docker inspect --format '{{.State.Status}}' "$(docker compose ps -q $service)")
            if [ "$state" == "running" ]; then
                 echo -e " ${GREEN}Running (no healthcheck)${NC}"
                 return 0
            fi
        fi
        
        echo -n "."
        sleep 2
        count=$((count+1))
    done
    
    echo -e " ${RED}Timeout!${NC}"
    return 1
}

wait_for_healthy postgres
wait_for_healthy redis
# Zookeeper usually starts fast, give it a moment
sleep 5

log_info "Starting Kafka..."
docker compose up -d kafka
wait_for_healthy kafka

log_info "Starting all other services..."
docker compose up -d

# Wait for core API
wait_for_healthy api

# 6. Initialize Database
log_info "Initializing database..."
# Run init script inside API container to ensure environment consistency
docker compose exec api python -m src.database.init_db

# 7. Create Kafka Topics
log_info "Creating Kafka topics..."
# Helper function to create topic
create_topic() {
    local topic=$1
    docker compose exec kafka kafka-topics --create \
        --topic "$topic" \
        --bootstrap-server localhost:9092 \
        --replication-factor 1 \
        --partitions 1 \
        --if-not-exists
}

create_topic "workflows"
create_topic "tasks"
create_topic "logs"
create_topic "metrics"

# 8. Final Status
log_info "---------------------------------------------------"
log_info "   AI Agent Framework Started Successfully! 🚀"
log_info "---------------------------------------------------"
echo -e "   ${BLUE}API Service:${NC}       http://localhost:8000"
echo -e "   ${BLUE}Airflow UI:${NC}        http://localhost:8080 (admin/admin)"
echo -e "   ${BLUE}MinIO Console:${NC}     http://localhost:9001 (minioadmin/minioadmin)"
echo -e "   ${BLUE}Prometheus:${NC}        http://localhost:9090"
echo -e "   ${BLUE}Grafana:${NC}           http://localhost:3000"
echo -e ""
log_info "To stop services, run: docker compose down"

