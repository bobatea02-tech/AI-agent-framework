# Operations Manual 🛠️

## 1. System Overview
The AI Agent Framework is a containerized microservices application.
*   **Service Manager**: Docker Compose
*   **Database**: PostgreSQL 15
*   **Message Broker**: Kafka
*   **AI Engine**: Intel OpenVINO on Workload Executors

## 2. Startup & Shutdown
**Start Production:**
```bash
docker compose -f docker-compose.prod.yml up -d
```
(Note: Ensure you have created `docker-compose.prod.yml` or use standard and override)

**Stop:**
```bash
docker compose down
```

## 3. Configuration Management
*   Secrets and configuration are stored in `.env`.
*   **NEVER** commit `.env` to version control.
*   Use `.env.production` as the source of truth for the live environment.

## 4. Maintenance
### Database Backups
Automated backups should be scheduled via cron (Linux) or Task Scheduler (Windows).
Manual Backup:
```bash
python scripts/backup_db.py
```
Manual Restore:
```bash
python scripts/restore_db.py backups/db_backup_YYYYMMDD.sql
```

### Log Rotation
Logs are rotated automatically by the `logging` module in Python (max 10MB x 5 files).
Docker logs should be configured with `json-file` driver limits in `docker-compose.yml`:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 5. Troubleshooting
*   **Service Down?**: Check `docker compose ps` and `docker compose logs <service>`.
*   **Slow Performance?**: Check Grafana dashboard for high latency or memory leaks.
*   **Kafka Issues**: If consumers stop consuming, verify consumer group status or restart the `airflow-worker` service.

## 6. Support Contacts
*   **DevOps Lead**: devops@example.com
*   **Emergency**: +1-555-0199
