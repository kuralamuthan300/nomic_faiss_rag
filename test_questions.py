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
        "question": "What are the three specific advantages of the Feature Adaptation Network (FAN) over conventional FSR as listed in the text?",
        "expected": ["joint learning scheme", "training with paired/unpaired data", "alleviating background/PIE"],
        "semantic": False,
    },

    # Question 2 — direct / literal
    {
        "question": "According to the document's breakdown of Faster R-CNN, how many anchors are present at the position (320, 320) of an image with size (600, 800)?",
        "expected": ["9", "nine"],   
        "semantic": False,
    },

    # Question 3 — direct / literal
    {
        "question": "According to the document's explanation of the Bag-of-Words model, what are the exact integer vectors generated for the sentences 'It is going to rain today' and 'Today I am not going outside'?",
        "expected": ["REPLACE_WITH_EXACT_VECTOR_1", "REPLACE_WITH_EXACT_VECTOR_2"], # Replace with the exact array values from your document
        "semantic": False,
    },

    # Question 4 — SEMANTIC (question vocabulary ≠ document vocabulary)
    {
        "question": "How does the document explain the concept of penalizing a predictive model for including useless predictor variables?",
        "expected": ["Adjusted R-Square", "junk independent variable"],   
        "semantic": True,
    },

    # Question 5 — SEMANTIC (question vocabulary ≠ document vocabulary)
    {
        "question": "What specific dataset was assembled by gathering internet clips of people making physical mistakes, and what was the main self-guided learning objective used to analyze it?",
        "expected": ["Oops!", "predict the speed of the video", "fail videos"],   
        "semantic": True,
    },
]
