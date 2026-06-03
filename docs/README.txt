Place your PDF files in this folder.

The RAG application will automatically discover and index all *.pdf files
found here when it starts up.

Supported:
  - Text-based PDFs (natively extracted with PyMuPDF / fitz)
  - Multi-page documents
  - Multiple files

Not supported:
  - Scanned image-only PDFs (no extractable text layer)
    → These are skipped with a warning.

After adding PDFs, restart the server:
  python app.py
