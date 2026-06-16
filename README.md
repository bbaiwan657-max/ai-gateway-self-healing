# AI Gateway - Self-Healing Proxy

A high-performance, self-healing AI model routing gateway with automatic failover across multiple providers.

## Features

- **Multi-Provider Routing**: Automatic routing across Agnes Merchant, Agnes Personal, NVIDIA, and AWS
- **Circuit Breaker Pattern**: Automatic failover when providers hit rate limits or errors
- **Self-Healing**: Guardian daemon monitors and auto-restarts the gateway on failures
- **Rate Limiting**: Built-in RPM tracking for all providers
- **OpenAI Compatible**: Standard `/v1/chat/completions` endpoint
- **Docker Support**: Containerized deployment with health checks

## Quick Start

### Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env` (already created)

3. Run with guardian (recommended):
```bash
python guardian.py
```

Or run directly:
```bash
python main.py
```

### Docker Setup

```bash
docker build -t ai-gateway .
docker run -p 8000:8000 --env-file .env ai-gateway
```

## API Usage

### Headers
- `Authorization: Bearer <LOCAL_AUTH_TOKEN>`

### Example Request
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer cascade-auto-heal-token-x9k2m4n7p1q3w5r8t0u2v4y6z8a0b2c4d6e8f0g2h4j6" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'
```

## Provider Priority

1. **Agnes Merchant** (2x RPM limit)
2. **Agnes Personal** (100-150 TPS)
3. **NVIDIA** (40 RPM)
4. **AWS** (Backup)

## Health Checks

- Gateway health: `GET /health`
- Provider status: `GET /providers/status`

## Architecture

- `main.py`: FastAPI gateway with routing logic
- `guardian.py`: Self-healing daemon process
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container configuration

## Security

- All API keys loaded from environment variables
- `.env` file in `.gitignore`
- Token-based authentication required
