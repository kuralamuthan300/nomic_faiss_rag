"""
test_questions.py — The 5 validation test questions.

INSTRUCTIONS FOR THE USER:
  After adding your PDFs and seeing the document segments (run: python ingest.py),
  update the questions below to match facts from YOUR documents.

  Each question must have:
    - "question":  the question string
    - "expected":  list of lowercase words/numbers ALL of which must appear in
                   the answer WITH search on, and NONE of which should appear in
                   the answer WITHOUT search.
    - "semantic":  True if this is a semantic question (question uses different
                   vocabulary than the target document passage)

  At least 2 questions must have "semantic": True.

HOW TO VERIFY A QUESTION IS SEMANTIC:
  1. Find the sentence(s) in the document that hold the answer.
  2. Remove common filler words (the, a, an, is, was, how, what, did, etc.).
  3. Check: do ANY meaningful words appear in both the question and that document text?
  4. If yes → not semantic. Reword the question using synonyms / conceptual phrasing.

EXAMPLE QUESTIONS (replace these with facts from YOUR documents):
  The placeholders below will return "FAIL" until replaced.
  The test runner prints the actual answers so you can copy the expected terms.
"""

# ─────────────────────────────────────────────────────────────────────────────
# REPLACE ALL 5 QUESTIONS WITH FACTS FROM YOUR OWN PDFs
# ─────────────────────────────────────────────────────────────────────────────

TEST_QUESTIONS = [
    # Question 1 — direct / literal (vocabulary shared with document)
    {
        "question": "REPLACE_ME: e.g. What learning rate was used during training?",
        "expected": ["REPLACE_ME"],   # e.g. ["0.001"]
        "semantic": False,
    },

    # Question 2 — direct / literal
    {
        "question": "REPLACE_ME: e.g. What dataset was used for evaluation?",
        "expected": ["REPLACE_ME"],   # e.g. ["imagenet"]
        "semantic": False,
    },

    # Question 3 — direct / literal
    {
        "question": "REPLACE_ME: e.g. How many parameters does the model have?",
        "expected": ["REPLACE_ME"],   # e.g. ["175b", "175 billion"]
        "semantic": False,
    },

    # Question 4 — SEMANTIC (question vocabulary ≠ document vocabulary)
    {
        "question": "REPLACE_ME: e.g. What mechanism prevented the network from over-relying on specific neurons?",
        "expected": ["REPLACE_ME"],   # e.g. ["dropout", "0.5"]
        "semantic": True,
    },

    # Question 5 — SEMANTIC (question vocabulary ≠ document vocabulary)
    {
        "question": "REPLACE_ME: e.g. What numerical threshold separates the two performance tiers described?",
        "expected": ["REPLACE_ME"],   # e.g. ["0.85", "85%"]
        "semantic": True,
    },
]
