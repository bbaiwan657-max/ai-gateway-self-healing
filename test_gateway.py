import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GATEWAY_URL = "http://localhost:8000"
AUTH_TOKEN = os.getenv("LOCAL_AUTH_TOKEN")

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{GATEWAY_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_providers_status():
    """Test providers status endpoint"""
    print("Testing providers status endpoint...")
    response = requests.get(f"{GATEWAY_URL}/providers/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_chat_completion():
    """Test chat completion endpoint"""
    print("Testing chat completion endpoint...")
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello! Can you help me?"}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {str(e)}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("AI Gateway Test Suite")
    print("=" * 50)
    print()
    
    test_health()
    test_providers_status()
    test_chat_completion()
    
    print("=" * 50)
    print("Test suite completed!")
    print("=" * 50)
