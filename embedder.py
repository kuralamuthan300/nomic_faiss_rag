"""
embedder.py — Build and query a FAISS index via the LLM Gateway V7 embed endpoint.

Gateway: POST http://localhost:8107/v1/embed
  body:  { "text": "...", "task_type": "retrieval_document" | "retrieval_query" }
  resp:  { "embedding": [...768 floats...], "dim": 768, ... }

Index:
  - Built once at startup from all document chunks.
  - Stored in memory only (rebuilt every run so the index always matches the docs).
  - Similarity: cosine (vectors are L2-normalised before inner-product search).

Public API:
  build_index(chunks)           → IndexStore
  search(store, query, top_k)   → list of (chunk_dict, score)
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
import numpy as np

GATEWAY_EMBED_URL = "http://localhost:8107/v1/embed"
EMBED_DIM = 768
TOP_K_DEFAULT = 3


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _embed(text: str, task_type: str = "retrieval_document") -> list[float]:
    """
    Call the gateway embed endpoint and return a 768-dim float vector.
    Raises httpx.HTTPStatusError on non-2xx; raises RuntimeError on dim mismatch.
    """
    r = httpx.post(
        GATEWAY_EMBED_URL,
        json={"text": text, "task_type": task_type},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    vec = data["embedding"]
    if len(vec) != EMBED_DIM:
        raise RuntimeError(
            f"Expected {EMBED_DIM}-dim embedding, got {len(vec)} "
            f"(provider={data.get('provider')}, model={data.get('model')})"
        )
    return vec


def _normalise(v: np.ndarray) -> np.ndarray:
    """L2-normalise a 1-D or 2-D array of vectors (in-place-safe)."""
    if v.ndim == 1:
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return v / norms


# ---------------------------------------------------------------------------
# public data structure
# ---------------------------------------------------------------------------

@dataclass
class IndexStore:
    """Holds the FAISS index and the original chunk list in the same order."""
    chunks: list[dict]
    matrix: np.ndarray   # shape (N, 768), L2-normalised float32
    index: object        # faiss.IndexFlatIP


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def build_index(chunks: list[dict]) -> IndexStore:
    """
    Embed every chunk and build a FAISS IndexFlatIP (inner-product) index.
    Because vectors are L2-normalised, inner product == cosine similarity.
    """
    try:
        import faiss
    except ImportError:
        raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")

    if not chunks:
        raise ValueError("No chunks to index. Add PDF files to the docs/ folder.")

    print(f"[embedder] Embedding {len(chunks)} chunks via {GATEWAY_EMBED_URL} …")
    vectors = []
    for i, chunk in enumerate(chunks):
        try:
            vec = _embed(chunk["text"], task_type="retrieval_document")
            vectors.append(vec)
            if (i + 1) % 10 == 0 or i == len(chunks) - 1:
                print(f"[embedder]   {i + 1}/{len(chunks)} embedded")
            # Small pause to respect rate limits on the fallback (Gemini: 5 RPM / 5 s cooldown)
            time.sleep(0.1)
        except Exception as exc:
            print(f"[embedder] ERROR embedding chunk {chunk['chunk_id']}: {exc}")
            # Use a zero vector as placeholder; it will never be the top result
            vectors.append([0.0] * EMBED_DIM)

    matrix = np.array(vectors, dtype=np.float32)
    matrix = _normalise(matrix)

    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(matrix)

    print(f"[embedder] Index built: {index.ntotal} vectors, dim={EMBED_DIM}")
    return IndexStore(chunks=chunks, matrix=matrix, index=index)


def search(
    store: IndexStore,
    query: str,
    top_k: int = TOP_K_DEFAULT,
) -> list[tuple[dict, float]]:
    """
    Embed the query (task_type=retrieval_query) and return the top-k
    most similar chunks as [(chunk_dict, cosine_score), …].
    """
    vec = _embed(query, task_type="retrieval_query")
    q = _normalise(np.array([vec], dtype=np.float32))

    scores, indices = store.index.search(q, min(top_k, store.index.ntotal))

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0:
            results.append((store.chunks[idx], float(score)))
    return results


# ---------------------------------------------------------------------------
# sanity check (standalone)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Tell me about the document"
    print(f"Query: {query}")
    print(f"Embedding test via {GATEWAY_EMBED_URL} …")
    try:
        vec = _embed(query, task_type="retrieval_query")
        print(f"OK — dim={len(vec)}, first 5 values: {vec[:5]}")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
