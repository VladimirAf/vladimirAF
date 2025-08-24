#!/usr/bin/env bash
set -euo pipefail

RAG_URL="${RAG_URL:-http://localhost:8000}"

curl -sS -X POST "$RAG_URL/ingest" \
  -H 'Content-Type: application/json' \
  -d '{"force_recreate": false}' | jq .

echo "Ingestion triggered."