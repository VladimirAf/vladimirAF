#!/usr/bin/env bash
set -euo pipefail

echo "Stopping RAG container..."
docker stop rag_service 2>/dev/null || true

echo "Removing RAG container..."
docker rm rag_service 2>/dev/null || true

echo "Building RAG service..."
docker-compose build rag

echo "Starting RAG service..."
docker-compose up -d rag

echo "Waiting for service to start..."
sleep 10

echo "Testing service..."
python3 test_rag.py
