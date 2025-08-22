"""Tiny TF-IDF retrieval over caregiver tips (local, no internet)."""
from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TinyRAG:
    def __init__(self, tips_dir: str):
        self.sections: List[Dict] = []
        self._load_sections(Path(tips_dir))
        texts = [s["text"] for s in self.sections] or ["general calming support tips for caregiver"]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.doc_matrix = self.vectorizer.fit_transform(texts)

    def _load_sections(self, tips_dir: Path):
        fp = tips_dir / "tips.md"
        if not fp.exists():
            self.sections = [{"title": "General", "text": "Stay calm and reduce stimuli."}]
            return
        txt = fp.read_text(encoding="utf-8")
        blocks = re.split(r"\n## +", txt)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            if block.startswith("## "):
                lines = block.split("\n", 1)
                title = lines[0].strip("# ").strip()
                body = lines[1] if len(lines) > 1 else ""
            else:
                title = "General"
                body = block
            self.sections.append({"title": title, "text": body})

    def query(self, query_text: str, k: int = 3) -> List[Dict]:
        q = self.vectorizer.transform([query_text])
        sims = cosine_similarity(q, self.doc_matrix).ravel()
        idxs = sims.argsort()[::-1][:k]
        return [
            {"title": self.sections[i]["title"], "snippet": self.sections[i]["text"][:400], "score": float(sims[i])}
            for i in idxs
        ]
