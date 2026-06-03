"""
test_questions.py — The 5 validation test questions.

Each question must have:
  - "question":  the question string
  - "expected":  list of lowercase words/numbers ALL of which must appear in
                 the answer WITH search on, and NONE of which should appear in
                 the answer WITHOUT search.
  - "semantic":  True if this is a semantic question (question uses different
                 vocabulary than the target document passage)
"""

TEST_QUESTIONS = [
    # Question 1 — FAN: Feature Adaptation Network (in Data Science Interview Preparation.pdf)
    {
        "question": "What are the three specific advantages of the Feature Adaptation Network (FAN) over conventional FSR as listed in the text?",
        "expected": ["joint learning scheme", "paired and unpaired", "disentangled identity"],
        "semantic": False,
    },

    # Question 2 — Faster R-CNN anchors (in Data Science Interview Preparation(#DAY 14).pdf)
    {
        "question": "According to the document's breakdown of Faster R-CNN, how many anchors are present at the position (320, 320) of an image with size (600, 800)?",
        "expected": ["nine", "9"],
        "semantic": False,
    },

    # Question 3 — Bag-of-Words vectors (in Data Science Interview Preparation Questions(#Day06).pdf)
    {
        "question": "According to the document's explanation of the Bag-of-Words model, what are the exact integer vectors generated for the sentences 'It is going to rain today' and 'Today I am not going outside'?",
        "expected": ["1, 1, 1, 1, 1, 1, 0, 0, 0, 0", "0, 0, 1, 0, 0, 1, 1, 1, 1, 1"],
        "semantic": False,
    },

    # Question 4 — SEMANTIC: R-Square problem with junk variables (in Data Science INterview Questions #Day1.pdf)
    {
        "question": "How does the document explain the concept of penalizing a predictive model for including useless predictor variables?",
        "expected": ["R-Square", "junk independent variables"],
        "semantic": True,
    },

    # Question 5 — SEMANTIC: Oops! Unintentional Action dataset (in Data Science Interview Interview Questions(#Day28).pdf)
    {
        "question": "What specific dataset was assembled by gathering internet clips of people making physical mistakes, and what was the main self-guided learning objective used to analyze it?",
        "expected": ["oops!", "predict the speed of the video", "fail"],
        "semantic": True,
    },
]