# Troubleshooting Guide 🔧

## Common Issues

### 1. `ModuleNotFoundError: No module named 'src'`
**Cause**: Python is running from the wrong directory or `PYTHONPATH` is not set.
**Solution**:
Always run commands from the project root (`ai-agent-framework/`).
```bash
# Correct
python -m src.api.main

# Incorrect
cd src/api && python main.py
```

### 2. Kafka Connection Failed
**Error**: `NoBrokersAvailable` or `ConnectionRefused`
**Solution**:
1.  Ensure Zookeeper is running *before* Kafka.
2.  Check docker logs: `docker compose logs kafka`
3.  If running locally (not docker), ensure `localhost:9092` is accessible.

### 3. Airflow Permission Denied
**Error**: `mkdir: cannot create directory '/opt/airflow/logs': Permission denied`
**Solution**:
Set the `AIRFLOW_UID` in your `.env` file to match your host user.
```bash
echo "AIRFLOW_UID=$(id -u)" >> .env
```

### 4. Database Connection Errors
**Error**: `psycopg2.OperationalError: connection to server... failed`
**Solution**:
1.  Ensure Postgres is healthy: `docker compose ps postgres`
2.  Check `.env` variables match `docker-compose.yml` credentials.
3.  On startup, the API might try to connect before DB is ready. The startup script handles this, but manual runs might need a retry loop or `wait-for-it` script.

## Debugging

### finding Logs
*   **API**: `docker compose logs -f api`
*   **Worker**: `docker compose logs -f airflow-worker`
*   **Database**: `docker compose logs -f postgres`

### Inspecting State
You can manually inspect the Redis state using `redis-cli`:

```bash
docker compose exec redis redis-cli
127.0.0.1:6379> KEYS *
1) "execution:550e8400-e29b..."
127.0.0.1:6379> GET "execution:550e8400-e29b..."
```

## Performance Tuning

*   **Slow Tasks**: Check if `LLMExecutor` is timing out. Increase `timeout` in your workflow JSON.
*   **Kafka Lag**: Scale up workers if the `workflows` topic has high lag.
