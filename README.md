# Nomic + FAISS RAG Application

A local Retrieval-Augmented Generation system that lets you ask questions about
PDF documents. Uses **Nomic Embed Text** (via LLM Gateway V7) for semantic search
and a local FAISS index for fast vector retrieval.
UI powered by **Gradio** (runs on port 7860).

---

## Prerequisites — Services That Must Be Running

| Service | Port | Purpose |
|---|---|---|
| **LLM Gateway V7** | `8107` | Embed endpoint (`/v1/embed`) + Chat endpoint (`/v1/chat`) |
| **Ollama** | `11434` | Hosts `nomic-embed-text` model for free local embeddings |

Start the gateway:
```bash
cd /path/to/llm_gatewayV7
./run.sh
```

Pull the embedding model (first time only):
```bash
ollama pull nomic-embed-text
```

Verify both are up:
```bash
curl -s http://localhost:8107/v1/embedders | python3 -m json.tool
```

---

## Quick Start

### 1. Install Python packages (with uv)

Make sure you have [uv](https://docs.astral.sh/uv/) installed, then:

```bash
cd /path/to/nomic_faiss_rag
uv sync
```

This creates a virtual environment (`.venv/`) and installs all dependencies
automatically (defined in `pyproject.toml`).

> **Tip:** Use `uv run python <script.py>` to run scripts without manually
> activating the virtual environment. For example: `uv run python ingest.py`.

### 2. Add your PDF files
```
docs/
  your_document.pdf
  another_paper.pdf
```

### 3. Preview document segments (optional but recommended)
```bash
uv run python ingest.py
```
This shows the first 10 chunks extracted from your PDFs — use this to write
good test questions.

### 4. Test the embedding service
```bash
uv run python embedder.py "test query"
```

### 5. Write your 5 test questions
Edit `test_questions.py` — replace the `REPLACE_ME` placeholders with real
facts from **your** documents. See the file for detailed instructions.

### 6. Start the application
```bash
uv run python app.py
```

### 7. Open the Gradio UI
[http://localhost:7860](http://localhost:7860)

---

## How It Works

```
User question
    │
    ▼
[Embed question]  ← LLM Gateway V7 /v1/embed (nomic-embed-text, 768-dim)
    │
    ▼
[FAISS cosine search]  ← top-3 most similar chunks
    │
    ├── context found → [LLM answer with context]  ← Gateway /v1/chat
    │                       strict system prompt: use ONLY context
    │
    └── RAG off     → [LLM answer from memory]   ← Gateway /v1/chat
                          plain system prompt
```

---

## File Layout

```
nomic_faiss_rag/
├── .gitignore          # Files excluded from version control
├── pyproject.toml      # Project metadata + dependencies (uv)
├── requirements.txt    # Python dependencies (legacy, kept for reference)
├── app.py              # Gradio UI + startup logic
├── ingest.py           # PDF reader + text chunker
├── embedder.py         # FAISS index builder + search
├── rag.py              # Answer generator (with / without RAG)
├── test_questions.py   # The 5 validation test questions  ← EDIT THIS
└── docs/               # ← PUT YOUR PDFs HERE
    └── README.txt
```

---

## Writing Good Test Questions

The plan requires **5 questions**, at least **2 of which must be "semantic"**
(different vocabulary than the source text).

### Steps
1. Run `uv run python ingest.py` to see chunk previews.
2. Find 5 specific facts (numbers, names, technical terms) in your documents.
3. For each fact, write a question. For 2 of them, rephrase using completely
   different words (synonyms, conceptual phrasing).
4. Set the expected terms to specific strings a general LLM would not know.
5. Verify semantic questions: remove filler words from question AND target
   sentence — no meaningful word should appear in both.

### Semantic question test
```
Document: "A dropout rate of 0.5 was applied to the final layer."

Question (NOT semantic): "What dropout rate was applied?"
  → "dropout", "rate" appear in both → NOT semantic ✗

Question (semantic): "What technique prevented the network from relying on specific neurons?"
  → zero overlap in meaningful words → SEMANTIC ✓
```

---

## Validation Rules

| Check | Pass condition |
|---|---|
| Answer WITH search | All `expected` terms appear in the answer |
| Answer WITHOUT search | None of the `expected` terms appear in the answer |

All 5 questions must pass both checks for the system to be considered validated.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `[LLM Gateway unreachable]` | Start `llm_gatewayV7/run.sh` |
| `No PDF files found` | Add PDFs to `docs/` folder |
| `PDF has no readable text` | Use a text-based PDF (not scanned image) |
| Test questions all FAIL | Update `test_questions.py` with facts from your actual PDFs |
| Embed returns wrong dim | Do not change `EMBED_OLLAMA_MODEL` in gateway; rebuild from scratch if needed |
| Gemini rate limit (429) | The gateway auto-falls back to Ollama; wait a few seconds and retry |

---

## Port Reference

| Component | Port |
|---|---|
| This Gradio app | `7860` |
| LLM Gateway V7 | `8107` |
| Ollama | `11434` |