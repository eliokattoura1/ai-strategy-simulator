import os
import re
from typing import List

import tiktoken
import chromadb
from chromadb.utils import embedding_functions

RAG_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(RAG_DIR, "chroma_db")


def _sanitize_collection_name(name: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name.lower())
    sanitized = re.sub(r"_+", "_", sanitized).strip("_-")
    if len(sanitized) < 3:
        sanitized = sanitized + "_co"
    return sanitized[:63]


def _extract_text(file) -> str:
    name = getattr(file, "name", "").lower()
    if name.endswith(".pdf"):
        import PyPDF2
        reader = PyPDF2.PdfReader(file)
        return " ".join(page.extract_text() or "" for page in reader.pages)
    content = file.read()
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="replace")
    return content


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunks.append(enc.decode(tokens[start:end]))
        if end >= len(tokens):
            break
        start += chunk_size - overlap
    return chunks


def _get_collection(company_name: str):
    from config import OPENAI_API_KEY
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-small",
    )
    return client.get_or_create_collection(
        name=_sanitize_collection_name(company_name),
        embedding_function=openai_ef,
    )


def process_documents(files, company_name: str) -> int:
    collection = _get_collection(company_name)

    all_chunks: List[str] = []
    all_ids: List[str] = []
    chunk_idx = 0

    for file in files:
        text = _extract_text(file)
        print(f"[RAG] process_documents: file='{getattr(file, 'name', '?')}' extracted {len(text)} chars")
        if not text.strip():
            print("[RAG] process_documents: file produced no text — skipping")
            continue
        for chunk in _chunk_text(text):
            all_chunks.append(chunk)
            all_ids.append(f"chunk_{chunk_idx}")
            chunk_idx += 1

    if all_chunks:
        collection.add(documents=all_chunks, ids=all_ids)
        print(f"[RAG] process_documents: stored {len(all_chunks)} chunks for company='{company_name}'")
    else:
        print(f"[RAG] process_documents: no chunks to store for company='{company_name}'")

    return len(all_chunks)


def query_context(company_name: str, query: str, n_results: int = 5) -> str:
    try:
        collection = _get_collection(company_name)
        count = collection.count()
        print(f"[RAG] query_context: company='{company_name}' chunks_in_db={count} query='{query[:60]}...'")
        if count == 0:
            print("[RAG] query_context: collection is empty — no documents uploaded for this company")
            return ""
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
        )
        if results and results["documents"] and results["documents"][0]:
            text = "\n\n---\n\n".join(results["documents"][0])
            print(f"[RAG] query_context: returning {len(text)} chars — preview: {text[:200]!r}")
            return text
        print("[RAG] query_context: query returned no documents")
        return ""
    except Exception as e:
        print(f"[RAG] query_context ERROR: {type(e).__name__}: {e}")
        return ""


def clear_company_context(company_name: str) -> None:
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        client.delete_collection(_sanitize_collection_name(company_name))
    except Exception:
        pass
