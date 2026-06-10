from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re
from typing import Iterable


DEFAULT_CHUNK_SIZE_WORDS = 350
DEFAULT_OVERLAP_WORDS = 100


@dataclass
class Document:
    source_id: str
    source_name: str
    path: str
    text: str


@dataclass
class Chunk:
    chunk_id: str
    source_id: str
    source_name: str
    path: str
    chunk_index: int
    start_word: int
    end_word: int
    text: str


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_documents(documents_dir: str | Path = "documents") -> list[Document]:
    documents_path = Path(documents_dir)
    if not documents_path.exists():
        raise FileNotFoundError(f"Documents folder not found: {documents_path}")

    documents: list[Document] = []
    for index, path in enumerate(sorted(documents_path.glob("*.txt")), start=1):
        text = normalize_text(path.read_text(encoding="utf-8", errors="replace"))
        if not text:
            continue

        documents.append(
            Document(
                source_id=f"doc_{index:03d}",
                source_name=path.name,
                path=str(path),
                text=text,
            )
        )

    return documents


def split_words(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def chunk_document(
    document: Document,
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> list[Chunk]:
    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be greater than 0")
    if overlap_words < 0:
        raise ValueError("overlap_words cannot be negative")
    if overlap_words >= chunk_size_words:
        raise ValueError("overlap_words must be smaller than chunk_size_words")

    words = split_words(document.text)
    if not words:
        return []

    chunks: list[Chunk] = []
    step = chunk_size_words - overlap_words
    start = 0
    chunk_index = 0

    while start < len(words):
        end = min(start + chunk_size_words, len(words))
        chunk_words = words[start:end]
        chunks.append(
            Chunk(
                chunk_id=f"{document.source_id}_chunk_{chunk_index:03d}",
                source_id=document.source_id,
                source_name=document.source_name,
                path=document.path,
                chunk_index=chunk_index,
                start_word=start,
                end_word=end,
                text=" ".join(chunk_words),
            )
        )

        if end == len(words):
            break

        start += step
        chunk_index += 1

    return chunks


def chunk_documents(
    documents: Iterable[Document],
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, chunk_size_words, overlap_words))
    return chunks


def save_chunks(
    chunks: list[Chunk],
    output_path: str | Path = "chunks.json",
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> None:
    output = {
        "chunk_count": len(chunks),
        "chunk_size_words": chunk_size_words,
        "overlap_words": overlap_words,
        "chunks": [asdict(chunk) for chunk in chunks],
    }
    Path(output_path).write_text(json.dumps(output, indent=2), encoding="utf-8")
