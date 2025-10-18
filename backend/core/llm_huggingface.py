"""Local Hugging Face text generation integration.

Uses transformers pipelines with locally downloaded weights (no network access).
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline  # type: ignore
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "transformers (and torch) are required for Hugging Face local inference. "
        "Install them with `pip install transformers torch`."
    ) from exc

from .llm import LLMConfig, SYSTEM_PROMPT, build_prompt

logger = logging.getLogger(__name__)

_GENERATOR: Optional["pipeline"] = None
_ACTIVE_MODEL: Optional[str] = None


def _ensure_pipeline(model_id: str) -> "pipeline":
    global _GENERATOR, _ACTIVE_MODEL
    if _GENERATOR is not None and _ACTIVE_MODEL == model_id:
        return _GENERATOR

    logger.info("Loading Hugging Face model from %s", model_id)
    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_id, local_files_only=True)
    device = 0 if torch.cuda.is_available() else -1
    _GENERATOR = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device=device,
    )
    _ACTIVE_MODEL = model_id
    return _GENERATOR


def generate_with_huggingface(
    cfg: LLMConfig, user_text: str, risk: float, triggers: dict, tips: list[dict]
) -> str:
    model_id = cfg.model or "distilbert-base-uncased"
    generator = _ensure_pipeline(model_id)

    prompt = build_prompt(user_text, risk, triggers, tips)
    context = f"{SYSTEM_PROMPT}\n\n{prompt}\nAssistant:"
    outputs = generator(
        context,
        max_new_tokens=cfg.max_tokens,
        temperature=max(0.01, cfg.temperature),
        do_sample=cfg.temperature > 0,
        pad_token_id=generator.tokenizer.eos_token_id,
    )
    text = outputs[0]["generated_text"]
    reply = text[len(context) :].strip()
    if not reply:
        return "I’m here with you."
    return reply


__all__ = ["generate_with_huggingface"]
