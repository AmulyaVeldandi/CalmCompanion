# backend/core/llm.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class LLMConfig:
    provider: str = "none"  # "none" | "ollama" | "cloud"
    model: str = "llama3.1:8b-instruct"  # for ollama
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 200

SYSTEM_PROMPT = """You are CalmCompanion, a gentle voice assistant for people living
with Alzheimer’s. Goals: (1) reduce agitation, (2) orient kindly, (3) offer one small,
practical step, (4) avoid medical advice/diagnosis. Style: short, calm, warm,
no jargon, no judgments. If safety concerns arise, encourage contacting a trusted
caregiver/professional. Keep replies under ~2 sentences when possible."""

def build_prompt(user_text: str, risk: float, triggers: dict, tips: list[dict]) -> str:
    tips_text = "\n".join(f"- {t['title']}: {t['snippet']}" for t in tips[:3]) or "- (no tips available)"
    trig_on = ", ".join([k for k, v in triggers.items() if v]) or "none detected"
    return f"""PATIENT SAID: {user_text}
RISK: {risk:.2f}
ACTIVE TRIGGERS: {trig_on}
CARE TIPS (summaries):
{tips_text}

Compose a brief, calming reply to the patient. Offer exactly one gentle option."""
