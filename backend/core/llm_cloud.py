# backend/core/llm_cloud.py
import os
from .llm import LLMConfig, SYSTEM_PROMPT, build_prompt

# Example skeleton; replace with your provider SDK
# e.g., from openai import OpenAI; client = OpenAI(api_key=cfg.api_key)
def generate_with_cloud(cfg: LLMConfig, user_text: str, risk: float, triggers: dict, tips: list[dict]) -> str:
    if not cfg.api_key or not cfg.endpoint:
        return "I’m here with you."
    prompt = build_prompt(user_text, risk, triggers, tips)
    # PSEUDOCODE: call your provider
    # resp = client.chat.completions.create(
    #    model=cfg.model,
    #    messages=[{"role":"system","content":SYSTEM_PROMPT},
    #              {"role":"user","content":prompt}],
    #    temperature=cfg.temperature, max_tokens=cfg.max_tokens
    # )
    # return resp.choices[0].message.content.strip()
    return "I’m here with you."  # placeholder if not configured
