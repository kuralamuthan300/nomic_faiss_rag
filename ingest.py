"""
ingest.py — Read PDFs from the docs/ folder and split into text chunks.

Splitting strategy:
  1. Split on double-newline (paragraph boundary).
  2. Split each paragraph into words.
  3. Build chunks of at most MAX_WORDS words, with OVERLAP_WORDS overlap between consecutive chunks.

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
MAX_WORDS = 400       # target words per chunk
OVERLAP_WORDS = 80    # words of overlap between consecutive chunks


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _chunk_text(text: str) -> list[str]:
    """Split text into chunks of at most MAX_WORDS words with OVERLAP_WORDS overlap."""
    paragraphs = re.split(r'\n{2,}', text)
    all_words = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Split paragraph into words (preserve spacing info via joins later)
        words = para.split()
        if not words:
            continue
        all_words.append(words)

    if not all_words:
        return []

    # Flatten word lists into a single list, tracking paragraph boundaries
    # We'll use a marker for paragraph breaks
    flat_words = []
    for i, wlist in enumerate(all_words):
        if i > 0:
            flat_words.append("__PARA_BREAK__")
        flat_words.extend(wlist)

    if MAX_WORDS <= 0:
        return [" ".join(flat_words).replace(" __PARA_BREAK__ ", "\n\n")]

    chunks = []
    start = 0
    while start < len(flat_words):
        end = min(start + MAX_WORDS, len(flat_words))
        # Build the chunk text from flat_words[start:end]
        segment_words = flat_words[start:end]
        # Reconstruct text: replace paragraph markers with double newline
        chunk_text = " ".join(segment_words).replace(" __PARA_BREAK__ ", "\n\n")
        chunks.append(chunk_text)
        start += MAX_WORDS - OVERLAP_WORDS

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