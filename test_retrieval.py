from __future__ import annotations

from embedding_retrieval import DEFAULT_TOP_K, retrieve_chunks


QUERIES = [
    "Where should I store my code?",
    "Should I use AI for my side project?",
    "How should I use GitHub tools to the fullest?",
]


def print_results(query: str, top_k: int = DEFAULT_TOP_K) -> None:
    print("=" * 80)
    print(f"Query: {query}")
    print("-" * 80)

    results = retrieve_chunks(query, top_k=top_k)
    for index, result in enumerate(results, start=1):
        preview = result.text.replace("\n", " ")
        if len(preview) > 500:
            preview = preview[:500] + "..."

        print(f"{index}. {result.source_name} chunk {result.chunk_index}")
        print(f"   distance: {result.distance:.4f}")
        print(f"   words: {result.start_word}-{result.end_word}")
        print(f"   text: {preview}")
        print()


def main() -> None:
    for query in QUERIES:
        print_results(query)


if __name__ == "__main__":
    main()
