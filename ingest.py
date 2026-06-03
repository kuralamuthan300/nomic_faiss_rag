"""
ingest.py — Read PDFs from the docs/ folder and split into text chunks.

Splitting strategy (matching the gateway README recommendation):
  1. Split on double-newline (paragraph boundary).
  2. If a paragraph is still > MAX_CHARS, split on sentence boundaries (". ").
  3. If a sentence is still > MAX_CHARS, hard-cut at MAX_CHARS.

Each chunk is tagged:
  {
      "text":     str,   # the chunk text
      "source":   str,   # PDF filename
      "chunk_id": str,   # "<stem>_<index>"
  }
"""

import re
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "docs"
MAX_CHARS = 3000   # well under the gateway's 8000-char limit


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _split_paragraph(para: str) -> list[str]:
    """Split one paragraph into sentence-level pieces, then hard-cut if needed."""
    # naive sentence split: ". " or "? " or "! "
    sentences = re.split(r'(?<=[.?!])\s+', para.strip())
    chunks, buf = [], ""
    for sent in sentences:
        if len(buf) + len(sent) + 1 <= MAX_CHARS:
            buf = (buf + " " + sent).strip()
        else:
            if buf:
                chunks.append(buf)
            # hard-cut a single sentence that is too long
            while len(sent) > MAX_CHARS:
                chunks.append(sent[:MAX_CHARS])
                sent = sent[MAX_CHARS:]
            buf = sent
    if buf:
        chunks.append(buf)
    return chunks


def _chunk_text(text: str) -> list[str]:
    """Split a full-document text into chunks respecting MAX_CHARS."""
    paragraphs = re.split(r'\n{2,}', text)
    chunks, buf = [], ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) > MAX_CHARS:
            # flush current buffer first
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.extend(_split_paragraph(para))
        elif len(buf) + len(para) + 2 <= MAX_CHARS:
            buf = (buf + "\n\n" + para).strip()
        else:
            if buf:
                chunks.append(buf)
            buf = para
    if buf:
        chunks.append(buf)
    return chunks


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def load_documents(docs_dir: Path = DOCS_DIR) -> list[dict]:
    """
    Return a list of chunk dicts from every PDF found in docs_dir.
    Raises FileNotFoundError if docs_dir does not exist.
    Returns an empty list (with a printed warning) if no PDFs are found.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        print(f"[ingest] Created docs directory: {docs_dir}")

    pdf_files = sorted(docs_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[ingest] WARNING: No PDF files found in {docs_dir}")
        return []

    all_chunks = []
    for pdf_path in pdf_files:
        print(f"[ingest] Processing: {pdf_path.name}")
        try:
            doc = fitz.open(str(pdf_path))
            pages_text = []
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text.strip():
                    pages_text.append(page_text)
                else:
                    print(f"[ingest]   Page {page_num + 1} has no extractable text (skipped)")
            doc.close()

            full_text = "\n\n".join(pages_text)
            if not full_text.strip():
                print(f"[ingest] WARNING: {pdf_path.name} has no readable text — skipping.")
                continue

            chunks = _chunk_text(full_text)
            stem = pdf_path.stem
            for idx, chunk_text in enumerate(chunks):
                all_chunks.append({
                    "text":     chunk_text,
                    "source":   pdf_path.name,
                    "chunk_id": f"{stem}_{idx}",
                })
            print(f"[ingest]   → {len(chunks)} chunks")

        except Exception as exc:
            print(f"[ingest] ERROR reading {pdf_path.name}: {exc} — skipping.")

    print(f"[ingest] Total chunks: {len(all_chunks)} from {len(pdf_files)} PDF(s)")
    return all_chunks


# ---------------------------------------------------------------------------
# CLI preview helper
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    chunks = load_documents()
    if not chunks:
        print("No chunks to display.")
        sys.exit(0)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"\n--- First {min(limit, len(chunks))} chunks ---")
    for c in chunks[:limit]:
        preview = c["text"][:200].replace("\n", " ")
        print(f"\n[{c['chunk_id']}] ({c['source']})")
        print(f"  {preview}...")
