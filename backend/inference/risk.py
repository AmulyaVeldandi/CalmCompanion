"""Heuristic risk scoring with trigger mapping and time-of-day prior."""
from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime

# Weights (tuned conservatively to avoid false positives)
W_NEG = 0.6
W_CUES = 0.8
W_LEN = 0.1
W_TIME = 0.2  # time-of-day prior (sundowning)

TRIGGERS: dict[str, list[str]] = {
    "confusion": ["where am i", "who are you", "don't remember", "can't remember", "lost"],
    "pain":      ["pain", "hurt", "ache", "dizzy", "headache", "burning", "nausea"],
    "loneliness":["alone", "lonely"],
    "overwhelm": ["stop it", "leave me alone", "get away"],
    "boredom":   ["bored"],
    "routine":   ["don't want to", "won't", "no i don't", "no i wont"],
    "environment":["too loud","noisy","crowd","crowded","too bright","too dark","clutter","hot","cold"],
    "physiology":["thirsty","hungry","bathroom","tired","sleepy","weak"],
    "anxiety":["scared","afraid","anxious","paranoid"],
}

def _time_prior(ts_iso: str) -> float:
    """Return a prior risk bump for late afternoon/evening (sundowning)."""
    try:
        hr = datetime.fromisoformat(ts_iso.replace("Z", "")).hour
    except Exception:
        hr = datetime.now().hour
    if 16 <= hr <= 22:
        return 1.0
    if 14 <= hr < 16 or 22 < hr <= 23:
        return 0.5
    return 0.0

def score_turn(sent_label: str, sent_score: float, cues: List[str], text: str, ts_iso: str | None = None) -> Dict[str, Any]:
    base = 0.0
    if sent_label == "negative":
        base += W_NEG * min(1.0, abs(sent_score) * 3.0)
    base += W_CUES * min(1.0, len(cues) / 3.0)
    base += W_LEN * min(1.0, len(text) / 200.0)
    if ts_iso:
        base += W_TIME * _time_prior(ts_iso)
    risk = max(0.0, min(1.0, base))

    low = text.lower()
    tmap = {k: any(kw in low for kw in kws) for k, kws in TRIGGERS.items()}

    # Provide an explanation payload
    explanation = {
        "signals": {
            "sentiment": sent_label,
            "sentiment_score": sent_score,
            "cue_count": len(cues),
            "time_prior": _time_prior(ts_iso) if ts_iso else 0.0,
        }
    }
    return {"risk": risk, "triggers": tmap, "explanation": explanation}

def summarize_window(turns: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not turns:
        return {"risk_avg": 0.0, "top_triggers": []}
    avg = sum(t["risk"] for t in turns) / len(turns)
    counts: dict[str, int] = {}
    for t in turns:
        for k, v in t["triggers"].items():
            if v:
                counts[k] = counts.get(k, 0) + 1
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]
    return {"risk_avg": avg, "top_triggers": [k for k, _ in top]}
