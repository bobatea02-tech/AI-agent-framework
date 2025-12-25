# Deployment Guide 🚀

This guide covers deployment strategies for the AI Agent Framework, from local Docker Compose to production Kubernetes and Cloud environments.

## 1. Local Deployment (Docker Compose)
Best for development and testing.

```bash
# Start all services
./scripts/startup.sh

# Stop services
docker compose down
```

## 2. Kubernetes Deployment ☸️
For production workloads, we recommend Kubernetes.

### Prerequisites
- kubectl configured
- A running Kubernetes cluster (EKS, GKE, AKS, or Minikube)

### Manifests
We provide sample manifests in `deploy/k8s/`.

**Deploy API:**
```bash
kubectl apply -f deploy/k8s/api.yaml
```

**Resource Requirements (per replica):**
- **CPU**: 250m request / 500m limit
- **Memory**: 512Mi request / 1Gi limit

### Scaling
Horizontal Pod Autoscaling (HPA) is recommended based on CPU usage or custom metrics (e.g., Kafka lag).

```bash
kubectl autoscale deployment ai-agent-api --cpu-percent=70 --min=2 --max=10
```

## 3. Cloud Infrastructure (Terraform) ☁️
Use our Terraform templates in `deploy/terraform/` to provision core infrastructure on AWS.

### Managed Services
We recommend using managed services for stateful components:
- **Database**: AWS RDS (PostgreSQL) / Google Cloud SQL
- **Cache**: AWS ElastiCache (Redis) / GCP Memorystore
- **Queue**: Amazon MSK (Kafka) / Confluent Cloud

### Provisioning
```bash
cd deploy/terraform
terraform init
terraform apply
```

## 4. Production Checklist ✅

### Security
- [ ] **Secrets Management**: Use Vault or AWS Secrets Manager. Do NOT commit `.env`.
- [ ] **Network Policies**: Restrict access to DB/Redis to only the K8s cluster.
- [ ] **HTTPS/TLS**: Terminate SSL at the Load Balancer/Ingress.

### Configuration
- [ ] **Environment Variables**:
    - Set `LOG_LEVEL=WARNING` or `INFO`
    - Set `AUTH_TYPE=oauth2` (if implemented)
    - Configure actual SMTP settings for Airflow alerts

### Monitoring & Observability
- [ ] **Prometheus**: Scrape `/metrics` endpoint.
- [ ] **Grafana**: Import dashboards for API latency and Workflow success rates.
- [ ] **Logging**: Ship logs to ELK/Datadog/CloudWatch.

### Backup
- [ ] **Database**: Enable automated daily backups (PITR).
- [ ] **MinIO/S3**: Enable versioning on storage buckets.

## 5. CI/CD Pipeline (GitHub Actions) 🔄
Example workflow `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ "main" ]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker Image
      run: docker build -t my-registry/ai-agent-api:${{ github.sha }} .
    - name: Push Image
      run: docker push my-registry/ai-agent-api:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
    - name: Update K8s
      run: |
        kubectl set image deployment/ai-agent-api api=my-registry/ai-agent-api:${{ github.sha }}
```
