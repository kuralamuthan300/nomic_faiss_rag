"""
test_questions.py — The 5 validation test questions (3 literal + 2 semantic).

Each question must have:
  - "question":  the question string
  - "expected":  list of lowercase words/numbers ALL of which must appear in
                 the answer WITH document search (RAG) on.
  - "semantic":  True if this question uses different vocabulary than the
                 target document passage (tests semantic retrieval, not keyword match).

Questions are designed to be answerable from the PDFs in the docs/ folder.
"""

TEST_QUESTIONS = [
    # Question 1 — basic R-Square concept (in Data Science Interview Questions #Day1.pdf)
    {
        "question": "What does R-Square measure in a regression model?",
        "expected": ["r-square", "variance"],
        "semantic": False,
    },

    # Question 2 — Faster R-CNN (in Data Science Interview Preparation(#DAY 14).pdf)
    {
        "question": "What does Faster R-CNN use to generate region proposals?",
        "expected": ["faster", "r-cnn", "region"],
        "semantic": False,
    },

    # Question 3 — Bag-of-Words (in Data Science Interview Preparation Questions(#Day06).pdf)
    {
        "question": "What is the Bag-of-Words model used for in text processing?",
        "expected": ["bag", "words", "vector"],
        "semantic": False,
    },

    # Question 4 — SEMANTIC: R-Square problem with junk variables (in Data Science Interview Questions #Day1.pdf)
    {
        "question": "How does the model get penalized for including useless predictor variables?",
        "expected": ["regularization"],
        "semantic": True,
    },

    # Question 5 — SEMANTIC: Oops! dataset (in Data Science Interview Interview Questions(#Day28).pdf)
    {
        "question": "What kind of video clips were collected to understand how people make mistakes?",
        "expected": ["video", "fail"],
        "semantic": True,
    },
]