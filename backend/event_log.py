from __future__ import annotations

import os
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Deque, Dict, List

_DEFAULT_LIMIT = int(os.getenv("EVENT_LOG_LIMIT", "200"))
_HARD_LIMIT = int(os.getenv("EVENT_LOG_HARD_LIMIT", "500"))
_MAX_LEN = max(_DEFAULT_LIMIT, _HARD_LIMIT)
_log: Deque[Dict[str, Any]] = deque(maxlen=_MAX_LEN)
_lock = Lock()


def add_event(kind: str, payload: Dict[str, Any]) -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "payload": payload,
    }
    with _lock:
        _log.appendleft(entry)


def get_events(limit: int | None = None) -> List[Dict[str, Any]]:
    with _lock:
        items = list(_log)
    if limit is None:
        return items
    return items[: max(0, min(limit, _MAX_LEN))]
