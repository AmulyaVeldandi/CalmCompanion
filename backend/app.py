from __future__ import annotations
import os
from backend.core.llm import LLMConfig
from backend.core import llm_ollama, llm_cloud, llm_huggingface

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from backend.core.config import settings
from backend.core.session_store import SessionStore, TurnRecord
from backend.inference.emotion import analyze_text
from backend.inference.risk import score_turn, summarize_window
from backend.inference.rag import TinyRAG
from backend.api import alexa_router
from backend.event_log import add_event, get_events
from backend.services import run_reasoning_agent, record_turn, aggregate_metrics

app = FastAPI(title=settings.app_name)
app.include_router(alexa_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = SessionStore()
rag = TinyRAG("backend/data/caregiver_guides")


llm_model = os.getenv("HF_MODEL_PATH") or os.getenv("LLM_MODEL", "llama3.1:8b-instruct")

llm_cfg = LLMConfig(
    provider=os.getenv("LLM_PROVIDER", "none"),        # "none" | "ollama" | "cloud"
    model=llm_model,
    api_key=os.getenv("LLM_API_KEY"),
    endpoint=os.getenv("LLM_ENDPOINT"),
    temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
    max_tokens=int(os.getenv("LLM_MAX_TOKENS", "200")),
)

class VoiceTurn(BaseModel):
    sid: str
    text: str
    timestamp: Optional[str] = None


class ReasonRequest(BaseModel):
    user_input: str
    context: Optional[Dict[str, Any]] = None


class ReasonResponse(BaseModel):
    plan: str

def _make_reply(triggers: Dict[str, bool]) -> str:
    if triggers.get("pain"):
        return "I’m sorry you’re uncomfortable. Would a short sit and some water help right now?"
    if triggers.get("confusion"):
        return "You’re safe. We are at home together. Would you like me to remind you what’s next?"
    if triggers.get("overwhelm") or triggers.get("environment"):
        return "Let’s slow down. We can move to a quieter, softer space. Would that help?"
    if triggers.get("loneliness") or triggers.get("anxiety"):
        return "I’m here with you. Would you like to listen to a favorite song or call someone?"
    if triggers.get("routine"):
        return "Let’s try one small step at a time. Would you like an easy first step?"
    if triggers.get("physiology"):
        return "Let’s check comfort. Would a sip of water or a bathroom break help?"
    return "Thank you for sharing. I’m here with you. Would a sip of water or some quiet time help?"

@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/reason", response_model=ReasonResponse)
def generate_reasoning_plan(payload: ReasonRequest) -> ReasonResponse:
    try:
        plan = run_reasoning_agent(payload.user_input, payload.context or {})
        add_event(
            "reason.success",
            {
                "user_input_preview": payload.user_input[:120],
                "context_keys": list((payload.context or {}).keys()),
                "plan_preview": plan[:240],
            },
        )
    except ValueError as exc:
        add_event(
            "reason.error",
            {
                "error": str(exc),
                "user_input_preview": payload.user_input[:120],
            },
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        add_event(
            "reason.error",
            {
                "error": str(exc),
                "user_input_preview": payload.user_input[:120],
            },
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected failures propagated
        add_event(
            "reason.error",
            {
                "error": str(exc),
                "user_input_preview": payload.user_input[:120],
            },
        )
        raise HTTPException(status_code=500, detail="Unexpected Bedrock agent failure.") from exc

    return ReasonResponse(plan=plan)

@app.post("/api/voice_chat")
def voice_chat(turn: VoiceTurn) -> dict:
    sid = turn.sid.strip() or "default"
    ts = turn.timestamp or datetime.now(timezone.utc).isoformat()
    sess = store.ensure(sid, created_at=ts)

    emo = analyze_text(turn.text)
    r = score_turn(emo["label"], emo["score"], emo["cues"], turn.text, ts_iso=ts)
    active = [k for k, v in r["triggers"].items() if v]
    q = " ".join(active) + " Alzheimer agitation caregiver tips" if active else "general calm tips"
    tips = rag.query(q, k=2)

    reply = None
    try:
        if llm_cfg.provider == "ollama":
            reply = llm_ollama.generate_with_ollama(llm_cfg, turn.text, r["risk"], r["triggers"], tips)
        elif llm_cfg.provider == "cloud":
            reply = llm_cloud.generate_with_cloud(llm_cfg, turn.text, r["risk"], r["triggers"], tips)
        elif llm_cfg.provider == "huggingface":
            reply = llm_huggingface.generate_with_huggingface(llm_cfg, turn.text, r["risk"], r["triggers"], tips)
    except Exception:
        reply = None

    if not reply or len(reply) > 400:
        reply = _make_reply(r["triggers"])

    rec = TurnRecord(ts=ts, text=turn.text, emotion=emo, risk=r, reply=reply, tips=tips)
    store.append(sid, rec)
    add_event(
        "voice_turn",
        {
            "sid": sid,
            "risk_score": r["risk"],
            "active_triggers": active,
            "reply_preview": reply[:160],
        },
    )
    record_turn(
        sid,
        rec,
        context={
            "turn_count": len(store.get_all(sid)),
            "active_triggers": active,
            "reason_model": llm_cfg.provider,
        },
    )

    return {
        "reply": reply,
        "risk": r["risk"],
        "triggers": r["triggers"],
        "tips": tips,
        "ts": ts,
        "turn_count": len(store.get_all(sid)),
        "explanation": r.get("explanation", {}),
    }

@app.get("/api/session_summary")
def session_summary(sid: str, window: int = settings.summary_window) -> dict:
    sess = store.get(sid)
    if not sess:
        return {"sid": sid, "created_at": None, "turns": [], "summary": {"risk_avg": 0.0, "top_triggers": []}, "count": 0}
    last = store.get_last(sid, max(1, window))
    turn_recs = [t.risk for t in last]
    summary = summarize_window(turn_recs) if last else {"risk_avg": 0.0, "top_triggers": []}
    # Keep payload small
    turns_payload = [
        {"ts": t.ts, "text": t.text, "risk": t.risk, "reply": t.reply, "tips": t.tips}
        for t in store.get_all(sid)[-settings.max_turns_kept:]
    ]
    return {
        "sid": sid,
        "created_at": sess.created_at,
        "turns": turns_payload,
        "summary": summary,
        "count": len(turns_payload),
    }


@app.get("/logs")
def get_logs(limit: int = 100) -> dict:
    safe_limit = max(1, min(limit, 500))
    events = get_events(safe_limit)
    return {"count": len(events), "logs": events}


@app.get("/analytics")
def analytics_dashboard() -> dict:
    return aggregate_metrics()
