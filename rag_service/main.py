import os
import hashlib
import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    from haystack.document_stores import FAISSDocumentStore  # type: ignore
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False

from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import EmbeddingRetriever, FARMReader
from haystack.pipelines import ExtractiveQAPipeline

load_dotenv()

DOCS_DIR = Path(os.getenv("DOCS_DIR", "/app/data_docs"))
INDEX_PATH = Path(os.getenv("INDEX_PATH", "/app/faiss_index/index.faiss"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

DOCS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="RAG Service", version="0.1.0")


class IngestRequest(BaseModel):
    force_recreate: bool = False


class QueryRequest(BaseModel):
    query: str
    top_k_retriever: int = 5
    top_k_reader: int = 3


class QueryResponse(BaseModel):
    answer: Optional[str]
    sources: List[dict]


HASH_DB_PATH = INDEX_PATH.parent / "ingestion_hashes.json"


def compute_file_sha256(path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_hash_db() -> dict:
    if HASH_DB_PATH.exists():
        return json.loads(HASH_DB_PATH.read_text())
    return {}


def save_hash_db(db: dict) -> None:
    HASH_DB_PATH.write_text(json.dumps(db, indent=2, ensure_ascii=False))


# Keep global store to avoid re-init on every request in local runs
_GLOBAL_STORE = None


def get_document_store():
    global _GLOBAL_STORE
    if _GLOBAL_STORE is not None:
        return _GLOBAL_STORE

    if FAISS_AVAILABLE:
        store = FAISSDocumentStore(
            faiss_index_factory_str="Flat",
            embedding_dim=384,
            sql_url="sqlite:///faiss_index/faiss.db",
            index="document",
            return_embedding=True,
            similarity="cosine",
        )
    else:
        store = InMemoryDocumentStore(embedding_dim=384, return_embedding=True, similarity="cosine")
    _GLOBAL_STORE = store
    return store


def get_retriever_reader(document_store):
    retriever = EmbeddingRetriever(
        document_store=document_store,
        embedding_model=EMBEDDING_MODEL,
        use_gpu=False,
        model_format="sentence_transformers",
    )
    reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=False)
    return retriever, reader


@app.post("/ingest")
def ingest(req: IngestRequest):
    document_store = get_document_store()
    retriever, _ = get_retriever_reader(document_store)

    if req.force_recreate:
        document_store.delete_documents()

    hash_db = load_hash_db()

    files = []
    for path in DOCS_DIR.rglob("*"):
        if path.is_file() and not path.name.startswith("."):
            files.append(path)

    new_or_changed = []
    for path in files:
        digest = compute_file_sha256(path)
        key = str(path.relative_to(DOCS_DIR))
        if hash_db.get(key) != digest:
            new_or_changed.append((key, path, digest))

    docs_to_write = []
    for key, path, digest in new_or_changed:
        meta = {"source": key, "sha256": digest}
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        if text.strip():
            docs_to_write.append({"content": text, "meta": meta})

    if docs_to_write:
        document_store.write_documents(docs_to_write)
        document_store.update_embeddings(retriever)
        for key, _, digest in new_or_changed:
            hash_db[key] = digest
        save_hash_db(hash_db)

    return {
        "ingested_files": [key for key, _, _ in new_or_changed],
        "total_files": len(files),
        "added": len(docs_to_write),
        "faiss": FAISS_AVAILABLE,
    }


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    document_store = get_document_store()
    retriever, reader = get_retriever_reader(document_store)
    pipe = ExtractiveQAPipeline(reader=reader, retriever=retriever)

    prediction = pipe.run(
        query=req.query,
        params={
            "Retriever": {"top_k": req.top_k_retriever},
            "Reader": {"top_k": req.top_k_reader},
        },
    )

    answers = prediction.get("answers", [])
    best = answers[0] if answers else None
    answer_text = best.answer if best else None

    sources = []
    for ans in answers:
        if ans.meta:
            sources.append({
                "source": ans.meta.get("source"),
                "score": ans.score,
                "context": ans.context,
            })

    return QueryResponse(answer=answer_text, sources=sources)

from fastapi import UploadFile, File


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    target_path = DOCS_DIR / file.filename
    content = file.file.read()
    target_path.write_bytes(content)
    hash_db = load_hash_db()
    key = str(target_path.relative_to(DOCS_DIR))
    if key in hash_db:
        del hash_db[key]
        save_hash_db(hash_db)
    return {"uploaded": file.filename}