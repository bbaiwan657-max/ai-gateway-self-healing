# AI Gateway - Self-Healing Proxy

A high-performance, self-healing AI model routing gateway with automatic failover across multiple providers.

## Features

- **Multi-Provider Routing**: Automatic routing across Agnes Merchant, Agnes Personal, NVIDIA, and AWS
- **Circuit Breaker Pattern**: Automatic failover when providers hit rate limits or errors
- **Self-Healing**: Guardian daemon monitors and auto-restarts the gateway on failures
- **Rate Limiting**: Built-in RPM tracking for all providers
- **OpenAI Compatible**: Standard `/v1/chat/completions` endpoint
- **Docker Support**: Containerized deployment with health checks
- **50ms Seamless Failover**: Automatic provider switching within 50ms

## Quick Start

### Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env` (use `.env.example` as template)

3. Run with guardian (recommended):
```bash
python guardian.py
```

Or run directly:
```bash
python main.py
```

4. Test the gateway:
```bash
python test_gateway.py
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

1. **Agnes Merchant** (2x RPM limit - 120 RPM)
2. **Agnes Personal** (100-150 TPS - 60 RPM)
3. **NVIDIA** (40 RPM)
4. **AWS** (Backup - 1000 RPM)

## Health Checks

- Gateway health: `GET /health`
- Provider status: `GET /providers/status`

## Architecture

- `main.py`: FastAPI gateway with routing logic
- `guardian.py`: Self-healing daemon process
- `test_gateway.py`: Test suite for validation
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container configuration

## Security

### ⚠️ CRITICAL SECURITY WARNING

**NEVER COMMIT .ENV FILE TO GIT OR ANY VERSION CONTROL SYSTEM**

The `.env` file contains sensitive API keys, tokens, and credentials that must remain private. 

**Security Rules:**
- **.env is already in .gitignore** - Do not remove this line
- **Never hardcode credentials** in Python files or any code
- **Use environment variables** for all sensitive data
- **Rotate compromised keys** immediately if accidentally exposed
- **Review .gitignore** before committing to ensure no secrets are tracked

**Built-in Security Features:**
- **Automatic Security Checks**: The application runs security audits on startup
- **Pre-commit Hooks**: Git hooks prevent accidental commits of secrets
- **Secret Detection**: Scans code for hardcoded credentials
- **Environment Validation**: Ensures .env is properly configured

**Security Checklist:**
- [ ] .env file exists and is configured
- [ ] .env is in .gitignore
- [ ] No hardcoded secrets in Python files
- [ ] Security checks pass on startup
- [ ] Pre-commit hooks are installed

### Security Implementation

- All API keys loaded from environment variables
- `.env` file in `.gitignore`
- Token-based authentication required
- `.env.example` provided for setup reference
- Automatic security validation on startup
- Pre-commit hooks for secret detection

## Auto-Healing Features

- **Dependency Detection**: Automatically installs missing Python packages
- **Port Conflict Resolution**: Automatically kills conflicting processes
- **Error Analysis**: Analyzes logs to determine failure causes
- **Auto-Restart**: Restarts gateway with cooldown period
- **Circuit Breaker**: Prevents cascading failures

## GitHub Repository

https://github.com/bbaiwan657-max/ai-gateway-self-healing
