from __future__ import annotations

import argparse
from pathlib import Path


#chunk size is in injestion overlap is 100 chunk size is 350
from ingestion import (
    DEFAULT_CHUNK_SIZE_WORDS,
    DEFAULT_OVERLAP_WORDS,
    chunk_documents,
    load_documents,
    save_chunks,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load all .txt files from the documents folder and chunk them for retrieval."
    )
    parser.add_argument("--documents-dir", default="documents")
    parser.add_argument("--output", default="chunks.json")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE_WORDS)
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP_WORDS)
    args = parser.parse_args()

    documents = load_documents(args.documents_dir)
    chunks = chunk_documents(
        documents,
        chunk_size_words=args.chunk_size,
        overlap_words=args.overlap,
    )
    save_chunks(
        chunks,
        args.output,
        chunk_size_words=args.chunk_size,
        overlap_words=args.overlap,
    )

    print(f"Loaded {len(documents)} documents from {Path(args.documents_dir).resolve()}")
    print(f"Created {len(chunks)} chunks")
    print(f"Wrote chunk data to {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
