"""Small, self-contained labeled dataset for the sentiment classifier.

The dataset is intentionally tiny and shipped in-repo so the model can be
trained offline during environment setup without any network access or
external data downloads.
"""

from __future__ import annotations

POSITIVE = "positive"
NEGATIVE = "negative"

# (text, label) pairs. Kept small on purpose: the goal is a fully reproducible,
# offline, end-to-end demonstrable pipeline rather than state-of-the-art accuracy.
TRAINING_DATA: list[tuple[str, str]] = [
    ("I absolutely love this product, it works great", POSITIVE),
    ("This is the best experience I have ever had", POSITIVE),
    ("Fantastic quality and wonderful support", POSITIVE),
    ("I am so happy with the results", POSITIVE),
    ("Amazing performance, highly recommended", POSITIVE),
    ("The team did an excellent job, truly delightful", POSITIVE),
    ("What a brilliant and helpful tool", POSITIVE),
    ("Superb value and a joy to use", POSITIVE),
    ("Everything worked perfectly and exceeded expectations", POSITIVE),
    ("A great and pleasant experience overall", POSITIVE),
    ("I really enjoy using this every single day", POSITIVE),
    ("Incredible results, I could not be more pleased", POSITIVE),
    ("This is terrible and a complete waste of money", NEGATIVE),
    ("I hate how slow and buggy it is", NEGATIVE),
    ("Awful experience, would not recommend", NEGATIVE),
    ("The worst support I have ever dealt with", NEGATIVE),
    ("Very disappointing and frustrating to use", NEGATIVE),
    ("Poor quality and constant crashes", NEGATIVE),
    ("I am unhappy and want a refund", NEGATIVE),
    ("Completely useless and broken", NEGATIVE),
    ("A horrible and painful experience", NEGATIVE),
    ("This made me angry and annoyed", NEGATIVE),
    ("Dreadful performance and terrible design", NEGATIVE),
    ("I regret buying this, it is a disaster", NEGATIVE),
]


def load_training_data() -> tuple[list[str], list[str]]:
    """Return parallel lists of (texts, labels)."""
    texts = [text for text, _ in TRAINING_DATA]
    labels = [label for _, label in TRAINING_DATA]
    return texts, labels
