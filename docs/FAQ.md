# Q&A / Troubleshooting

## General

### Q: What is the AI Agent Framework?
**A:** It is a modular, event-driven platform for building, orchestrating, and deploying AI agents that can perform tasks like Form Filling, Q&A, and Tool usage.

### Q: Why use Kafka?
**A:** Kafka provides decoupling between the API (Producer) and the Agents (Consumers), allowing for massive horizontal scalability and buffering during load spikes.

## Intel OpenVINO

### Q: Do I need an Intel CPU?
**A:** OpenVINO runs on any CPU, but it is highly optimized for Intel Architectures (Core, Xeon) using AVX-512/AMX instructions.

### Q: How do I enable OpenVINO?
**A:** Set `USE_OPENVINO=true` in your environment variables or in the specific workflow configuration.

### Q: My download failed?
**A:** Ensure you have internet access and `openvino-dev` installed. Run `pip install openvino-dev`.

## Troubleshooting

### Q: API returns 401 Unauthorized?
**A:** You need to provide the `X-API-Key` header. Check your `.env` file for the `API_KEY_SECRET`.

### Q: Database connection failed?
**A:** Ensure your database container (Postgres) is running. Use `docker compose ps` to check status.
