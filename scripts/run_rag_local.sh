#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT/rag_service"

export DOCS_DIR="${DOCS_DIR:-$PROJECT_ROOT/data_docs}"
export INDEX_PATH="${INDEX_PATH:-$PROJECT_ROOT/faiss_index/index.faiss}"
export EMBEDDING_MODEL="${EMBEDDING_MODEL:-sentence-transformers/all-MiniLM-L6-v2}"

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000