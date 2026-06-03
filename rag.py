"""
rag.py — Generate answers with and without document context.

With RAG:
  1. Search the FAISS index for the top-k most relevant chunks.
  2. Build a context block from those chunks.
  3. Send the question + context to the LLM Gateway V7 (/v1/chat).
  4. Return the answer text plus the retrieved chunk metadata.

Without RAG:
  1. Send the question directly to the LLM Gateway V7 (/v1/chat).
  2. Return just the answer text.

Both paths use the gateway's auto_route="memory" hint so the gateway picks the
appropriate worker model based on the prompt size.
"""

from __future__ import annotations

import httpx

GATEWAY_CHAT_URL = "http://localhost:8107/v1/chat"
TOP_K = 3

RAG_SYSTEM = (
    "You are a precise question-answering assistant. "
    "Answer the user's question using ONLY the provided document context. "
    "If the context does not contain the answer, say: "
    "\"The documents do not contain enough information to answer this question.\" "
    "Do not use any prior knowledge."
)

PLAIN_SYSTEM = (
    "You are a helpful assistant. Answer the question from your general knowledge."
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _chat(prompt: str, system: str) -> str:
    """POST to /v1/chat and return the text field."""
    body = {
        "prompt": prompt,
        "system": system,
        "max_tokens": 1024,
        "temperature": 0.7,
        "auto_route": "memory",
    }
    try:
        r = httpx.post(GATEWAY_CHAT_URL, json=body, timeout=120)
        r.raise_for_status()
        return r.json().get("text", "").strip()
    except httpx.HTTPStatusError as e:
        return f"[LLM Gateway error {e.response.status_code}]: {e.response.text[:300]}"
    except httpx.RequestError as e:
        return f"[LLM Gateway unreachable]: {e}"


def _build_context(results: list[tuple[dict, float]]) -> str:
    """Format retrieved chunks into a readable context block."""
    parts = []
    for rank, (chunk, score) in enumerate(results, start=1):
        parts.append(
            f"[Source {rank}: {chunk['source']} | chunk {chunk['chunk_id']} | "
            f"relevance {score:.3f}]\n{chunk['text']}"
        )
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def answer_with_rag(
    question: str,
    store,              # embedder.IndexStore
    top_k: int = TOP_K,
) -> dict:
    """
    Return:
      {
        "answer":   str,
        "sources":  [{"source", "chunk_id", "score", "preview"}, …]
      }
    """
    from embedder import search  # avoid circular import at module level

    results = search(store, question, top_k=top_k)

    if not results:
        return {
            "answer": "No relevant document segments were found for your question.",
            "sources": [],
        }

    context = _build_context(results)
    prompt = (
        f"Document context:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer based only on the context above:"
    )

    answer = _chat(prompt, system=RAG_SYSTEM)

    sources = [
        {
            "source":   chunk["source"],
            "chunk_id": chunk["chunk_id"],
            "score":    round(score, 4),
            "preview":  chunk["text"][:300].replace("\n", " "),
        }
        for chunk, score in results
    ]

    return {"answer": answer, "sources": sources}


def answer_without_rag(question: str) -> dict:
    """
    Return:
      {
        "answer": str,
        "sources": []
      }
    """
    answer = _chat(question, system=PLAIN_SYSTEM)
    return {"answer": answer, "sources": []}


# ---------------------------------------------------------------------------
# service health check helpers (used by app.py on startup)
# ---------------------------------------------------------------------------

def check_embed_service() -> tuple[bool, str]:
    """Ping the embed endpoint with a trivial string."""
    try:
        r = httpx.post(
            "http://localhost:8107/v1/embed",
            json={"text": "ping", "task_type": "retrieval_query"},
            timeout=10,
        )
        if r.status_code == 200:
            return True, "OK"
        return False, f"HTTP {r.status_code}"
    except httpx.RequestError as e:
        return False, str(e)


def check_chat_service() -> tuple[bool, str]:
    """Ping the chat endpoint with a trivial prompt."""
    try:
        r = httpx.post(
            GATEWAY_CHAT_URL,
            json={"prompt": "Say OK", "max_tokens": 4},
            timeout=30,
        )
        if r.status_code == 200:
            return True, "OK"
        return False, f"HTTP {r.status_code}"
    except httpx.RequestError as e:
        return False, str(e)
