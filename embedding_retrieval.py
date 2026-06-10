from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.errors import NotFoundError
from sentence_transformers import SentenceTransformer


DEFAULT_CHUNKS_PATH = "chunks.json"
DEFAULT_CHROMA_PATH = "chroma_db"
DEFAULT_COLLECTION_NAME = "side_project_guide_chunks"
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_TOP_K = 5


@dataclass
class RetrievalResult:
    chunk_id: str
    text: str
    distance: float
    source_name: str
    chunk_index: int
    start_word: int
    end_word: int


def load_chunks(chunks_path: str | Path = DEFAULT_CHUNKS_PATH) -> list[dict[str, Any]]:
    path = Path(chunks_path)
    if not path.exists():
        raise FileNotFoundError(f"Chunks file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    chunks = data.get("chunks", [])
    if not chunks:
        raise ValueError(f"No chunks found in {path}")

    return chunks


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def get_chroma_collection(
    chroma_path: str | Path = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
):
    client = chromadb.PersistentClient(path=str(chroma_path))
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def reset_chroma_collection(
    chroma_path: str | Path = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
):
    client = chromadb.PersistentClient(path=str(chroma_path))
    try:
        client.delete_collection(name=collection_name)
    except (ValueError, NotFoundError):
        pass
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def build_metadata(chunk: dict[str, Any]) -> dict[str, str | int]:
    return {
        "source_id": chunk["source_id"],
        "source_name": chunk["source_name"],
        "path": chunk["path"],
        "chunk_index": int(chunk["chunk_index"]),
        "start_word": int(chunk["start_word"]),
        "end_word": int(chunk["end_word"]),
    }


def embed_and_store_chunks(
    chunks_path: str | Path = DEFAULT_CHUNKS_PATH,
    chroma_path: str | Path = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    model_name: str = DEFAULT_MODEL_NAME,
    reset_collection: bool = True,
) -> int:
    chunks = load_chunks(chunks_path)
    model = get_embedding_model(model_name)
    collection = (
        reset_chroma_collection(chroma_path, collection_name)
        if reset_collection
        else get_chroma_collection(chroma_path, collection_name)
    )

    ids = [chunk["chunk_id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [build_metadata(chunk) for chunk in chunks]
    embeddings = model.encode(documents, normalize_embeddings=True).tolist()

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return len(chunks)


def retrieve_chunks(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    chroma_path: str | Path = DEFAULT_CHROMA_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    model_name: str = DEFAULT_MODEL_NAME,
) -> list[RetrievalResult]:
    if not query.strip():
        raise ValueError("query cannot be empty")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    model = get_embedding_model(model_name)
    collection = get_chroma_collection(chroma_path, collection_name)
    if collection.count() == 0:
        raise ValueError(
            "The Chroma collection is empty. Run `python build_vector_store.py` "
            "before running retrieval."
        )

    query_embedding = model.encode([query], normalize_embeddings=True).tolist()[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    retrieved: list[RetrievalResult] = []
    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        retrieved.append(
            RetrievalResult(
                chunk_id=chunk_id,
                text=text,
                distance=float(distance),
                source_name=str(metadata["source_name"]),
                chunk_index=int(metadata["chunk_index"]),
                start_word=int(metadata["start_word"]),
                end_word=int(metadata["end_word"]),
            )
        )

    return retrieved
