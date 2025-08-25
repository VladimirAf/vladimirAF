# RAG + Rasa Ticket Assistant

Stack: Haystack (FAISS) + FastAPI service for RAG, Rasa 3.x bot with custom action.

## Quick start

1. Put your documents into `data_docs/` (plain text/markdown preferred).
2. Start services:
```bash
bash scripts/run_all.sh
```
3. Trigger first ingestion:
```bash
bash scripts/update.sh
```
4. Chat with Rasa HTTP API (or via `rasa shell` inside the container):
```bash
curl -s "http://localhost:5005/webhooks/rest/webhook" \
  -H 'Content-Type: application/json' \
  -d '{"sender":"test","message":"найди инструкцию по установке"}' | jq .
```

## Daily updates
- Add new files to `data_docs/` or modify existing ones.
- Run `bash scripts/update.sh` or call POST `/ingest` on `http://localhost:8000`.
- Only changed/new files are embedded and indexed (sha256-based incremental).

## Environment
- Configure `.env` if needed (e.g., `OPENAI_API_KEY` for future LLM readers).
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.

## Folders
- `rag_service/`: FastAPI Haystack service
- `rasa_bot/`: Rasa project (stories, NLU, domain, actions)
- `data_docs/`: Your source documents
- `faiss_index/`: Persistent FAISS index and metadata

## Notes
- First run may download models (DPR/Reader). Keep internet access enabled.
- To rebuild: `docker compose build --no-cache`.
