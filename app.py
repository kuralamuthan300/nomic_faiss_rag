"""
app.py — Gradio UI for the Nomic + FAISS RAG application.

Tabs:
  1. Ask a Question  — text input, RAG toggle, answer + source chips
  2. Validation Tests — run all 5 questions, results in a DataFrame table

Startup (runs once before the UI is shown):
  1. Health-check embed + chat services via rag.py helpers.
  2. Load and chunk all PDFs from docs/.
  3. Build the FAISS index via embedder.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import gradio as gr
import pandas as pd

# Local modules
from ingest import load_documents, DOCS_DIR
from embedder import build_index
from rag import (
    answer_with_rag,
    answer_without_rag,
    check_embed_service,
    check_chat_service,
)
from test_questions import TEST_QUESTIONS

# ─── Global state ────────────────────────────────────────────────────────────
INDEX_STORE   = None
CHUNK_COUNT   = 0
DOC_COUNT     = 0
STARTUP_ERROR: str | None = None
# ─────────────────────────────────────────────────────────────────────────────

BANNER_CSS = """
<style>
  .status-ok   { color: #22d3a0; font-weight: 600; }
  .status-err  { color: #f87171; font-weight: 600; }
  .source-block {
    background: rgba(108,99,255,0.08);
    border: 1px solid rgba(108,99,255,0.25);
    border-radius: 8px; padding: 0.6rem 0.9rem;
    margin-bottom: 0.5rem; font-size: 0.82rem;
  }
  .src-meta { color: #6c63ff; font-weight: 600; margin-bottom: 0.2rem; }
  .src-preview { color: #94a3b8; font-style: italic; }
</style>
"""

CUSTOM_CSS = """
.gradio-container { max-width: 900px !important; margin: 0 auto; }
.gr-button-primary { background: linear-gradient(135deg,#6c63ff,#8b5cf6) !important;
                     border: none !important; color: #fff !important; }
.gr-button-secondary { background: linear-gradient(135deg,#00c8ff,#06b6d4) !important;
                       border: none !important; color: #000 !important; }
footer { display: none !important; }
"""


# ---------------------------------------------------------------------------
# startup — runs before the UI is served
# ---------------------------------------------------------------------------

def _startup() -> None:
    global INDEX_STORE, CHUNK_COUNT, DOC_COUNT, STARTUP_ERROR

    print("[app] Checking services …")

    embed_ok, embed_msg = check_embed_service()
    if not embed_ok:
        STARTUP_ERROR = (
            f"Embedding service (LLM Gateway V7 on port 8107) is unreachable: "
            f"{embed_msg}.\n"
            f"Start it with:  cd /path/to/llm_gatewayV7 && ./run.sh"
        )
        print(f"[app] ERROR: {STARTUP_ERROR}")
        return

    chat_ok, chat_msg = check_chat_service()
    if not chat_ok:
        STARTUP_ERROR = (
            f"Chat service (LLM Gateway V7 on port 8107) is unreachable: "
            f"{chat_msg}.\n"
            f"Start it with:  cd /path/to/llm_gatewayV7 && ./run.sh"
        )
        print(f"[app] ERROR: {STARTUP_ERROR}")
        return

    print("[app] Services OK — loading documents …")
    chunks = load_documents(DOCS_DIR)
    DOC_COUNT = len({c["source"] for c in chunks})

    if not chunks:
        STARTUP_ERROR = (
            f"No PDF files found in {DOCS_DIR}.\n"
            f"Add at least one PDF and restart the server."
        )
        print(f"[app] WARNING: {STARTUP_ERROR}")
        return

    print("[app] Building FAISS index …")
    try:
        INDEX_STORE = build_index(chunks)
        CHUNK_COUNT = len(chunks)
        print(f"[app] Ready — {CHUNK_COUNT} chunks from {DOC_COUNT} document(s).")
    except Exception as exc:
        STARTUP_ERROR = f"Failed to build FAISS index: {exc}"
        print(f"[app] ERROR: {STARTUP_ERROR}")


# ---------------------------------------------------------------------------
# Tab 1 — Ask a Question
# ---------------------------------------------------------------------------

def _format_sources_html(sources: list[dict]) -> str:
    if not sources:
        return ""
    parts = ["<div style='margin-top:0.75rem'>"]
    parts.append(
        "<div style='font-size:0.72rem;font-weight:600;color:#64748b;"
        "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem'>"
        f"📄 {len(sources)} document segment{'s' if len(sources) != 1 else ''} used</div>"
    )
    for i, s in enumerate(sources, 1):
        preview = s["preview"].replace("<", "&lt;").replace(">", "&gt;")
        parts.append(
            f"<div class='source-block'>"
            f"<div class='src-meta'>Source {i}: {s['source']} — "
            f"chunk {s['chunk_id']} — relevance {s['score']:.3f}</div>"
            f"<div class='src-preview'>\"{preview}…\"</div>"
            f"</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def ask_question(question: str, use_rag: bool) -> tuple[str, str]:
    """
    Returns (answer_text, sources_html).
    Called by the Gradio submit button.
    """
    question = (question or "").strip()
    if not question:
        return "⚠ Please enter a question.", ""

    if STARTUP_ERROR:
        return f"⚠ Service error:\n{STARTUP_ERROR}", ""

    if use_rag:
        if INDEX_STORE is None:
            return "⚠ Index not available — check startup logs.", ""
        result = answer_with_rag(question, INDEX_STORE)
    else:
        result = answer_without_rag(question)

    sources_html = _format_sources_html(result.get("sources", []))
    return result["answer"], sources_html


# ---------------------------------------------------------------------------
# Tab 2 — Validation Tests
# ---------------------------------------------------------------------------

def run_tests() -> tuple[str, pd.DataFrame]:
    """
    Returns (summary_markdown, results_dataframe).
    Called by the Gradio button.
    """
    if STARTUP_ERROR:
        return f"⚠ **Service error:** {STARTUP_ERROR}", pd.DataFrame()
    if INDEX_STORE is None:
        return "⚠ **Index not available** — check startup logs.", pd.DataFrame()

    rows = []
    all_passed = True

    for i, tq in enumerate(TEST_QUESTIONS, 1):
        question    = tq["question"]
        expected    = [e.lower() for e in tq["expected"]]
        is_semantic = tq.get("semantic", False)

        # with RAG
        rag_res    = answer_with_rag(question, INDEX_STORE)
        rag_answer = rag_res["answer"].lower()
        rag_passed = all(term in rag_answer for term in expected)

        # without RAG
        plain_res    = answer_without_rag(question)
        plain_answer = plain_res["answer"].lower()
        plain_passed = not any(term in plain_answer for term in expected)

        both = rag_passed and plain_passed
        if not both:
            all_passed = False

        rows.append({
            "#":              i,
            "Question":       question[:90] + ("…" if len(question) > 90 else ""),
            "Expected":       ", ".join(expected),
            "Type":           "Semantic" if is_semantic else "Literal",
            "With Search":    "✓ PASS" if rag_passed   else "✗ FAIL",
            "Without Search": "✓ PASS" if plain_passed else "✗ FAIL",
            "Overall":        "✓ PASS" if both         else "✗ FAIL",
            "With Answer":    rag_res["answer"][:200],
            "Without Answer": plain_res["answer"][:200],
        })

    passed_count = sum(1 for r in rows if r["Overall"] == "✓ PASS")
    total        = len(rows)

    if all_passed:
        summary = f"### ✅ All {total} tests passed — system is working correctly."
    else:
        summary = f"### ❌ {passed_count} / {total} tests passed. See table for details."

    df = pd.DataFrame(rows)
    return summary, df


# ---------------------------------------------------------------------------
# Status banner (shown at the top of every tab)
# ---------------------------------------------------------------------------

def _status_banner() -> str:
    if STARTUP_ERROR:
        return (
            f"<div style='background:rgba(248,113,113,0.1);border:1px solid "
            f"rgba(248,113,113,0.35);border-radius:10px;padding:0.85rem 1.1rem;"
            f"margin-bottom:0.5rem'>"
            f"<span class='status-err'>⚠ Service Error</span><br>"
            f"<span style='font-size:0.85rem;color:#e2e8f0'>{STARTUP_ERROR}</span></div>"
        )
    return (
        f"<div style='background:rgba(34,211,160,0.08);border:1px solid "
        f"rgba(34,211,160,0.25);border-radius:10px;padding:0.75rem 1.1rem;"
        f"margin-bottom:0.5rem'>"
        f"<span class='status-ok'>✦ Ready</span> — "
        f"<span style='font-size:0.85rem;color:#94a3b8'>"
        f"{CHUNK_COUNT} chunks indexed from {DOC_COUNT} "
        f"document{'s' if DOC_COUNT != 1 else ''}</span></div>"
    )


# ---------------------------------------------------------------------------
# Build the Gradio app
# ---------------------------------------------------------------------------

def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Nomic + FAISS RAG",
    ) as demo:

        gr.HTML(BANNER_CSS)
        gr.Markdown(
            "# ⚡ Nomic + FAISS RAG\n"
            "Ask questions about your PDF documents using semantic vector search."
        )
        gr.HTML(_status_banner())

        # ── Tab 1 — Ask ──────────────────────────────────────────────────
        with gr.Tab("🔍 Ask a Question"):
            with gr.Row():
                with gr.Column(scale=3):
                    question_box = gr.Textbox(
                        label="Your Question",
                        placeholder=(
                            "e.g. What mechanism prevented the network from "
                            "over-relying on specific neurons?"
                        ),
                        lines=3,
                        elem_id="question-input",
                    )
                with gr.Column(scale=1, min_width=160):
                    rag_toggle = gr.Checkbox(
                        value=True,
                        label="Document Search ON",
                        info="Uncheck to answer from LLM memory only",
                        elem_id="rag-toggle",
                    )

            ask_btn = gr.Button("Ask", variant="primary", elem_id="ask-btn")

            with gr.Group():
                answer_out = gr.Textbox(
                    label="Answer",
                    lines=6,
                    interactive=False,
                    elem_id="answer-out",
                )
                sources_out = gr.HTML(label="Sources used", elem_id="sources-out")

            ask_btn.click(
                fn=ask_question,
                inputs=[question_box, rag_toggle],
                outputs=[answer_out, sources_out],
                api_name="ask",
            )
            # Also submit on Enter
            question_box.submit(
                fn=ask_question,
                inputs=[question_box, rag_toggle],
                outputs=[answer_out, sources_out],
            )

            gr.Markdown(
                "> **Tip:** Ask the same question twice — once with Search ON, "
                "once with Search OFF — to see the difference RAG makes."
            )

        # ── Tab 2 — Tests ────────────────────────────────────────────────
        with gr.Tab("🧪 Validation Tests"):
            gr.Markdown(
                "Runs all 5 test questions automatically.\n\n"
                "- **With Search** — answer must contain all expected terms.\n"
                "- **Without Search** — answer must NOT contain any expected terms.\n"
                "- Edit `test_questions.py` to add facts from your own PDFs."
            )

            test_btn = gr.Button(
                "▶ Run All 5 Tests", variant="secondary", elem_id="test-btn"
            )

            summary_out = gr.Markdown(elem_id="test-summary")

            results_df = gr.Dataframe(
                headers=[
                    "#", "Question", "Expected", "Type",
                    "With Search", "Without Search", "Overall",
                    "With Answer", "Without Answer",
                ],
                datatype=["number", "str", "str", "str",
                          "str", "str", "str", "str", "str"],
                interactive=False,
                wrap=True,
                elem_id="results-table",
            )

            test_btn.click(
                fn=run_tests,
                inputs=[],
                outputs=[summary_out, results_df],
                api_name="run_tests",
            )

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _startup()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7860
    print(f"[app] Launching Gradio on http://localhost:{port}")
    ui = build_ui()
    ui.launch(
        server_name="0.0.0.0",
        server_port=port,
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.purple,
            secondary_hue=gr.themes.colors.cyan,
            neutral_hue=gr.themes.colors.slate,
            font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui"],
        ).set(
            body_background_fill="*neutral_950",
            block_background_fill="*neutral_900",
            block_border_color="*neutral_800",
            input_background_fill="*neutral_800",
        ),
        css=CUSTOM_CSS,
    )
