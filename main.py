import asyncio
import os
import sys
import time
import random
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import httpx
from contextlib import asynccontextmanager
import logging
from functools import wraps
from dotenv import load_dotenv

# SECURITY CHECK: Run security audit before starting
try:
    import security_check
    if not security_check.run_security_checks():
        print("❌ Security checks failed. Application startup aborted.")
        sys.exit(1)
except ImportError:
    print("⚠️  Warning: security_check module not found. Skipping security checks.")
except Exception as e:
    print(f"⚠️  Warning: Security check error: {str(e)}. Continuing startup...")

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gateway.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
AGNES_MERCHANT_KEY = os.getenv("AGNES_MERCHANT_KEY")
AGNES_PERSONAL_KEY = os.getenv("AGNES_PERSONAL_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
LOCAL_AUTH_TOKEN = os.getenv("LOCAL_AUTH_TOKEN")

# API Endpoints
AGNES_BASE_URL = "https://api.agnes.ai/v1"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
AWS_BEDROCK_BASE_URL = "https://bedrock-runtime.us-east-1.amazonaws.com"

# Rate limiting tracking
rate_limit_tracker = {
    "merchant": {"last_reset": time.time(), "requests": 0, "rpm_limit": 120},
    "personal": {"last_reset": time.time(), "requests": 0, "rpm_limit": 60},
    "nvidia": {"last_reset": time.time(), "requests": 0, "rpm_limit": 40},
    "aws": {"last_reset": time.time(), "requests": 0, "rpm_limit": 1000}
}

# Circuit breaker state
circuit_breaker = {
    "merchant": {"failures": 0, "last_failure": 0, "state": "closed"},
    "personal": {"failures": 0, "last_failure": 0, "state": "closed"},
    "nvidia": {"failures": 0, "last_failure": 0, "state": "closed"},
    "aws": {"failures": 0, "last_failure": 0, "state": "closed"}
}

CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0

class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None

def verify_auth_token(auth_token: Optional[str] = Header(None)):
    if not auth_token or auth_token != LOCAL_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return auth_token

def check_rate_limit(provider: str) -> bool:
    current_time = time.time()
    tracker = rate_limit_tracker[provider]
    
    # Reset counter if minute has passed
    if current_time - tracker["last_reset"] >= 60:
        tracker["last_reset"] = current_time
        tracker["requests"] = 0
    
    if tracker["requests"] >= tracker["rpm_limit"]:
        return False
    
    tracker["requests"] += 1
    return True

def update_circuit_breaker(provider: str, success: bool):
    cb = circuit_breaker[provider]
    if success:
        cb["failures"] = 0
        cb["state"] = "closed"
    else:
        cb["failures"] += 1
        cb["last_failure"] = time.time()
        if cb["failures"] >= CIRCUIT_BREAKER_THRESHOLD:
            cb["state"] = "open"

def is_circuit_open(provider: str) -> bool:
    cb = circuit_breaker[provider]
    if cb["state"] == "open":
        if time.time() - cb["last_failure"] > CIRCUIT_BREAKER_TIMEOUT:
            cb["state"] = "half_closed"
            return False
        return True
    return False

async def call_agnes_merchant(request: ChatRequest) -> Dict[str, Any]:
    if is_circuit_open("merchant") or not check_rate_limit("merchant"):
        raise Exception("Circuit open or rate limit exceeded")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{AGNES_BASE_URL}/chat/completions",
                json=request.dict(),
                headers={
                    "Authorization": f"Bearer {AGNES_MERCHANT_KEY}",
                    "Content-Type": "application/json"
                }
            )
            if response.status_code == 429:
                update_circuit_breaker("merchant", False)
                raise Exception("Rate limit exceeded")
            response.raise_for_status()
            update_circuit_breaker("merchant", True)
            return response.json()
        except Exception as e:
            update_circuit_breaker("merchant", False)
            raise e

async def call_agnes_personal(request: ChatRequest) -> Dict[str, Any]:
    if is_circuit_open("personal") or not check_rate_limit("personal"):
        raise Exception("Circuit open or rate limit exceeded")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{AGNES_BASE_URL}/chat/completions",
                json=request.dict(),
                headers={
                    "Authorization": f"Bearer {AGNES_PERSONAL_KEY}",
                    "Content-Type": "application/json"
                }
            )
            if response.status_code == 429:
                update_circuit_breaker("personal", False)
                raise Exception("Rate limit exceeded")
            response.raise_for_status()
            update_circuit_breaker("personal", True)
            return response.json()
        except Exception as e:
            update_circuit_breaker("personal", False)
            raise e

async def call_nvidia(request: ChatRequest) -> Dict[str, Any]:
    if is_circuit_open("nvidia") or not check_rate_limit("nvidia"):
        raise Exception("Circuit open or rate limit exceeded")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                json={
                    **request.dict(),
                    "model": "nvidia/llama-3.1-405b-instruct"
                },
                headers={
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            if response.status_code == 429:
                update_circuit_breaker("nvidia", False)
                raise Exception("Rate limit exceeded")
            response.raise_for_status()
            update_circuit_breaker("nvidia", True)
            return response.json()
        except Exception as e:
            update_circuit_breaker("nvidia", False)
            raise e

async def call_aws(request: ChatRequest) -> Dict[str, Any]:
    if is_circuit_open("aws") or not check_rate_limit("aws"):
        raise Exception("Circuit open or rate limit exceeded")
    
    # Simplified AWS Bedrock call (would normally use boto3)
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # This is a placeholder - actual AWS Bedrock requires AWS SDK
            # For now, we'll simulate a response
            await asyncio.sleep(0.1)
            update_circuit_breaker("aws", True)
            return {
                "id": f"aws-{datetime.now().timestamp()}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "AWS backup channel activated. Please configure proper AWS Bedrock integration."
                    },
                    "finish_reason": "stop"
                }]
            }
        except Exception as e:
            update_circuit_breaker("aws", False)
            raise e

async def route_request(request: ChatRequest) -> Dict[str, Any]:
    providers = ["merchant", "personal", "nvidia", "aws"]
    
    for provider in providers:
        try:
            logger.info(f"Attempting provider: {provider}")
            if provider == "merchant":
                return await call_agnes_merchant(request)
            elif provider == "personal":
                return await call_agnes_personal(request)
            elif provider == "nvidia":
                return await call_nvidia(request)
            elif provider == "aws":
                return await call_aws(request)
        except Exception as e:
            logger.warning(f"Provider {provider} failed: {str(e)}")
            continue
    
    raise HTTPException(status_code=503, detail="All providers failed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Gateway starting up...")
    yield
    logger.info("Gateway shutting down...")

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/providers/status")
async def providers_status():
    return {
        "rate_limits": rate_limit_tracker,
        "circuit_breakers": circuit_breaker
    }

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    auth_token: str = Header(None, alias="Authorization")
):
    try:
        # Extract token from Bearer format if present
        if auth_token and auth_token.startswith("Bearer "):
            auth_token = auth_token[7:]
        
        if auth_token != LOCAL_AUTH_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        logger.info(f"Received chat completion request for model: {request.model}")
        
        if request.stream:
            return StreamingResponse(
                stream_response(request),
                media_type="text/event-stream"
            )
        else:
            response = await route_request(request)
            return JSONResponse(content=response)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_completions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_response(request: ChatRequest):
    providers = ["merchant", "personal", "nvidia", "aws"]
    
    for provider in providers:
        try:
            if provider == "merchant":
                response = await call_agnes_merchant(request)
            elif provider == "personal":
                response = await call_agnes_personal(request)
            elif provider == "nvidia":
                response = await call_nvidia(request)
            elif provider == "aws":
                response = await call_aws(request)
            
            # Convert to streaming format
            yield f"data: {response}\n\n"
            return
        except Exception as e:
            logger.warning(f"Streaming provider {provider} failed: {str(e)}")
            continue
    
    yield f"data: {{'error': 'All providers failed'}}\n\n"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
