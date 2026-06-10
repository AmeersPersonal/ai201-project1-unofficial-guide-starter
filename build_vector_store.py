from __future__ import annotations

import argparse

from embedding_retrieval import (
    DEFAULT_CHROMA_PATH,
    DEFAULT_CHUNKS_PATH,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_MODEL_NAME,
    embed_and_store_chunks,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed chunks with all-MiniLM-L6-v2 and store them in ChromaDB."
    )
    parser.add_argument("--chunks", default=DEFAULT_CHUNKS_PATH)
    parser.add_argument("--chroma-path", default=DEFAULT_CHROMA_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION_NAME)
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args()

    count = embed_and_store_chunks(
        chunks_path=args.chunks,
        chroma_path=args.chroma_path,
        collection_name=args.collection,
        model_name=args.model,
        reset_collection=not args.no_reset,
    )

    print(f"Embedded and stored {count} chunks in ChromaDB")
    print(f"Collection: {args.collection}")
    print(f"Chroma path: {args.chroma_path}")


if __name__ == "__main__":
    main()
