"""Basic sentiment and cue extraction.

This module keeps computation lightweight: a lexicon-based sentiment score
and a set of regular-expression cues tuned for agitation-related signals.
"""
from __future__ import annotations
from typing import Dict, Any, List
import re

NEG_WORDS = set(
    """worried anxious nervous agitated upset angry mad furious scared afraid sad lonely
    bored confused lost hurt pain ache dizzy headache frustrated annoyed overwhelmed
    thirsty hungry tired cold hot itchy burning nausea fever shiver weak dizzy""".split()
)
POS_WORDS = set(
    """happy calm relaxed okay good fine great loved safe comfortable content glad hopeful""".split()
)

AGITATION_CUES = [
    r"\b(where am i|what is this place|who are you)\b",
    r"\b(leave me alone|get away|stop it)\b",
    r"\b(i (won't|dont) want to|no i (won't|dont))\b",
    r"!!!|\?\?\?",
    r"\b(pain|hurt|ache|dizzy|headache|nausea|itchy|burning|fever|shiver)\b",
    r"\b(i'm lost|i am lost|can't remember|don'?t remember)\b",
    r"\b(too loud|too bright|too dark|crowd|crowded|noisy|clutter)\b",
    r"\b(thirsty|hungry|bathroom|tired|sleepy|cold|hot|weak)\b",
    r"\b(scared|afraid|anxious|lonely|embarrassed|paranoid)\b",
]

def analyze_text(text: str) -> Dict[str, Any]:
    """Return a dict with 'label', 'score', and 'cues'."""
    t = text.lower()
    tokens = re.findall(r"[a-z']+", t)
    pos = sum(1 for w in tokens if w in POS_WORDS)
    neg = sum(1 for w in tokens if w in NEG_WORDS)
    sent_score = (pos - neg) / max(len(tokens), 1)

    cues: List[str] = [pat for pat in AGITATION_CUES if re.search(pat, t)]

    if sent_score <= -0.03 or cues:
        label = "negative"
    elif sent_score >= 0.03:
        label = "positive"
    else:
        label = "neutral"

    return {"label": label, "score": round(sent_score, 3), "cues": cues}
