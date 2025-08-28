#!/usr/bin/env bash
set -euo pipefail

RAG_URL="${RAG_URL:-http://localhost:8000}"

echo "Testing RAG service health..."
if ! curl -sS -f "http://localhost:8000/health" > /dev/null; then
    echo "Error: RAG service is not responding to health check"
    exit 1
fi

echo "Triggering ingestion..."
response=$(curl -sS -w "\n%{http_code}" -X POST "http://localhost:8000/ingest" \
  -H 'Content-Type: application/json' \
  -d '{"force_recreate": false}')

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" -eq 200 ]; then
    echo "$body" | jq .
    echo "Ingestion completed successfully."
else
    echo "Error: HTTP $http_code"
    echo "Response: $body"
    exit 1
fi