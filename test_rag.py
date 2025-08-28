#!/usr/bin/env python3
import requests
import json

def test_health():
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health check status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_ingest():
    try:
        response = requests.post(
            "http://localhost:8000/ingest",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"force_recreate": False})
        )
        print(f"Ingest status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Ingest failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing RAG service...")
    
    if test_health():
        print("Health check passed")
        test_ingest()
    else:
        print("Health check failed")
