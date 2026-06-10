from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_LLM_MODEL = "grok-3-mini"
DEFAULT_TOP_K = 5
XAI_CHAT_COMPLETIONS_URL = "https://api.x.ai/v1/chat/completions"


SYSTEM_PROMPT = """You are The Tech Student's Unofficial Guide to Building Side Projects.
Answer only from the retrieved context. If the context does not contain enough information,
say what is missing and give the safest limited answer you can. Be practical, concise, and
student-friendly. Cite the source file names you used."""


def load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def format_context(results: list[object]) -> str:
    context_blocks = []
    for index, result in enumerate(results, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[Source {index}]",
                    f"File: {result.source_name}",
                    f"Chunk: {result.chunk_index}",
                    f"Distance: {result.distance:.4f}",
                    "Text:",
                    result.text,
                ]
            )
        )

    return "\n\n".join(context_blocks)


def get_grok_api_key() -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Grok API key is missing. Add GROK_API_KEY to your .env file."
        )
    return api_key


def call_grok_llm(
    question: str,
    context: str,
    model: str = DEFAULT_LLM_MODEL,
    temperature: float = 0.2,
) -> str:
    api_key = get_grok_api_key()

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Use the retrieved context below to answer the question.\n\n"
                    f"Question: {question}\n\n"
                    f"Retrieved context:\n{context}"
                ),
            },
        ],
    }

    request = Request(
        XAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Grok API request failed: {error.code} {details}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach Grok API: {error.reason}") from error

    return data["choices"][0]["message"]["content"].strip()


def print_sources(results: list[object]) -> None:
    print("\nSources:")
    seen = set()
    for result in results:
        key = (result.source_name, result.chunk_index)
        if key in seen:
            continue
        seen.add(key)
        print(
            f"- {result.source_name}, chunk {result.chunk_index} "
            f"(distance {result.distance:.4f})"
        )


def answer_question(question: str, top_k: int, model: str, show_context: bool) -> None:
    from embedding_retrieval import retrieve_chunks

    results = retrieve_chunks(question, top_k=top_k)
    context = format_context(results)

    if show_context:
        print("\nRetrieved context:")
        print(context)
        print("\n" + "=" * 80 + "\n")

    answer = call_grok_llm(question, context, model=model)
    print(answer)
    print_sources(results)


def interactive_loop(top_k: int, model: str, show_context: bool) -> None:
    print("The Tech Student's Unofficial Guide")
    print("Ask a question, or type 'exit' to quit.\n")

    while True:
        question = input("Question: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue

        try:
            answer_question(question, top_k, model, show_context)
        except Exception as error:
            print(f"Error: {error}", file=sys.stderr)
        print()


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Simple CLI for asking the side-project guide RAG system questions."
    )
    parser.add_argument("question", nargs="*", help="Question to ask. Omit for interactive mode.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--model",
        default=os.environ.get("GROK_MODEL")
        or os.environ.get("XAI_MODEL")
        or DEFAULT_LLM_MODEL,
    )
    parser.add_argument("--show-context", action="store_true")
    args = parser.parse_args()

    question = " ".join(args.question).strip()
    if question:
        answer_question(question, args.top_k, args.model, args.show_context)
    else:
        interactive_loop(args.top_k, args.model, args.show_context)


if __name__ == "__main__":
    main()
