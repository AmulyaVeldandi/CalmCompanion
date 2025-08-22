"""In-memory session store for demo purposes.

A session groups conversation turns under a session id (sid).
In production, replace with a database-backed store.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class TurnRecord:
    ts: str
    text: str
    emotion: Dict[str, Any]
    risk: Dict[str, Any]
    reply: str
    tips: list[dict]

@dataclass
class Session:
    sid: str
    created_at: str
    turns: List[TurnRecord] = field(default_factory=list)

class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def ensure(self, sid: str, created_at: str) -> Session:
        if sid not in self._sessions:
            self._sessions[sid] = Session(sid=sid, created_at=created_at)
        return self._sessions[sid]

    def append(self, sid: str, turn: TurnRecord) -> None:
        self._sessions[sid].turns.append(turn)

    def get_last(self, sid: str, n: int) -> list[TurnRecord]:
        return self._sessions[sid].turns[-n:] if sid in self._sessions else []

    def get_all(self, sid: str) -> list[TurnRecord]:
        return self._sessions[sid].turns if sid in self._sessions else []

    def get(self, sid: str) -> Session | None:
        return self._sessions.get(sid)
