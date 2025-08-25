#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m pip install --user --break-system-packages -r "$PROJECT_ROOT/rag_service/requirements-lite.txt"

echo "Local dependencies installed (lite, without FAISS)."