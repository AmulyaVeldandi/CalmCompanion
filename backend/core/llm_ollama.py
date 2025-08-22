# backend/core/llm_ollama.py
import requests, json, os
from .llm import LLMConfig, SYSTEM_PROMPT, build_prompt

def generate_with_ollama(cfg: LLMConfig, user_text: str, risk: float, triggers: dict, tips: list[dict]) -> str:
    prompt = build_prompt(user_text, risk, triggers, tips)
    body = {
        "model": cfg.model,
        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}",
        "options": {"temperature": cfg.temperature, "num_predict": cfg.max_tokens},
        "stream": False,
    }
    url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    r = requests.post(url, json=body, timeout=20)
    r.raise_for_status()
    data = r.json()
    return (data.get("response") or "").strip() or "I’m here with you."
