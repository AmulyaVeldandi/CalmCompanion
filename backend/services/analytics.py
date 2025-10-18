from __future__ import annotations

import hashlib
import json
import logging
import os
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock
from typing import Any, Deque, Dict, Iterable, List, Mapping, Optional

try:  # Optional: boto3 is recommended but module should degrade gracefully.
    import boto3  # type: ignore
    from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    boto3 = None  # type: ignore

    class BotoCoreError(Exception):
        pass

    class ClientError(Exception):
        pass

from backend.core.session_store import TurnRecord

logger = logging.getLogger(__name__)

_MAX_RECORDS = int(os.getenv("ANALYTICS_MAX_RECORDS", "1000"))
_records: Deque[Dict[str, Any]] = deque(maxlen=_MAX_RECORDS)
_lock = Lock()

_AWS_REGION = os.getenv("AWS_REGION")
_DDB_TABLE = os.getenv("ANALYTICS_DYNAMODB_TABLE")
_S3_BUCKET = os.getenv("ANALYTICS_S3_BUCKET")

_boto_session = None
if boto3 is not None and (_DDB_TABLE or _S3_BUCKET):
    try:
        _boto_session = boto3.session.Session(region_name=_AWS_REGION)
    except Exception as exc:  # pragma: no cover - environment specific
        logger.warning("Failed to initialize boto3 session: %s", exc)
        _boto_session = None


def _ensure_session() -> Optional["boto3.session.Session"]:
    global _boto_session
    if _boto_session is None and boto3 is not None:
        try:
            _boto_session = boto3.session.Session(region_name=_AWS_REGION)
        except Exception as exc:  # pragma: no cover - environment specific
            logger.warning("Unable to create boto3 session: %s", exc)
            _boto_session = None
    return _boto_session


def _decimalize(value: Any) -> Any:
    """Recursively convert floats to Decimal for DynamoDB compatibility."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, bool):
        return value
    if isinstance(value, Mapping):
        return {k: _decimalize(v) for k, v in value.items()}
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
        return [_decimalize(v) for v in value]
    return value


def _emit_to_dynamodb(item: Dict[str, Any]) -> None:
    if not _DDB_TABLE:
        return
    session = _ensure_session()
    if session is None:
        return
    try:
        client = session.resource("dynamodb")
        table = client.Table(_DDB_TABLE)
        table.put_item(Item=_decimalize(item))
    except (BotoCoreError, ClientError) as exc:  # pragma: no cover - network interaction
        logger.warning("Failed to write analytics item to DynamoDB: %s", exc)


def _emit_to_s3(item: Dict[str, Any]) -> None:
    if not _S3_BUCKET:
        return
    session = _ensure_session()
    if session is None:
        return
    day = item.get("turn_ts", item.get("ts", datetime.now(timezone.utc).isoformat()))[:10]
    key = f"analytics/{day}/{item['sid']}-{item['turn_hash']}-{item['turn_ts'].replace(':', '-')}.json"
    try:
        client = session.resource("s3")
        obj = client.Object(_S3_BUCKET, key)
        obj.put(Body=json.dumps(item).encode("utf-8"))
    except (BotoCoreError, ClientError) as exc:  # pragma: no cover - network interaction
        logger.warning("Failed to write analytics item to S3: %s", exc)


def record_turn(
    sid: str,
    turn: TurnRecord,
    context: Optional[Dict[str, Any]] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Store an anonymized snapshot of a conversational turn and emit to AWS sinks."""
    snapshot_ts = datetime.now(timezone.utc).isoformat()
    text_hash = hashlib.sha256(turn.text.encode("utf-8")).hexdigest()[:16]
    mood_label = turn.emotion.get("label") if isinstance(turn.emotion, Mapping) else None
    mood_score = turn.emotion.get("score") if isinstance(turn.emotion, Mapping) else None
    triggers = turn.risk.get("triggers", {}) if isinstance(turn.risk, Mapping) else {}
    actions_payload = actions or []

    entry = {
        "sid": sid,
        "ts": snapshot_ts,
        "turn_ts": turn.ts,
        "turn_hash": text_hash,
        "mood": mood_label,
        "mood_score": mood_score,
        "risk": turn.risk.get("risk") if isinstance(turn.risk, Mapping) else None,
        "triggers": triggers,
        "actions": actions_payload,
        "context": {
            "summary": context or {},
            "tips_count": len(turn.tips),
            "reply_preview": (turn.reply or "")[:120],
        },
    }

    with _lock:
        _records.append(entry)

    anonymized_entry = {
        **entry,
        "context": {
            **entry["context"],
            "summary": {k: v for k, v in (context or {}).items()},
        },
    }
    _emit_to_dynamodb(anonymized_entry)
    _emit_to_s3(anonymized_entry)
    return entry


def record_action(
    source: str,
    sid: Optional[str],
    action_payload: Dict[str, Any],
    plan_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Capture auxiliary actions, e.g. smart home automations."""
    snapshot_ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "sid": sid or "anon",
        "ts": snapshot_ts,
        "turn_ts": snapshot_ts,
        "turn_hash": hashlib.sha256(f"{source}-{snapshot_ts}".encode("utf-8")).hexdigest()[:16],
        "mood": None,
        "mood_score": None,
        "risk": None,
        "triggers": {},
        "actions": [action_payload],
        "context": {
            "summary": {"source": source},
            "tips_count": 0,
            "reply_preview": (plan_text or "")[:120],
        },
    }

    with _lock:
        _records.append(entry)

    _emit_to_dynamodb(entry)
    _emit_to_s3(entry)
    return entry


def aggregate_metrics() -> Dict[str, Any]:
    """Return lightweight aggregate analytics for dashboards or SageMaker exploration."""
    with _lock:
        data = list(_records)

    if not data:
        return {
            "total_turns": 0,
            "sessions_tracked": 0,
            "mood_counts": {},
            "avg_risk": 0.0,
            "recent_actions": [],
            "triggers_by_day": {},
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    mood_counter: Counter[str] = Counter()
    risk_values: List[float] = []
    triggers_by_day: defaultdict[str, Counter[str]] = defaultdict(Counter)
    action_counter: Counter[str] = Counter()

    for item in data:
        mood = item.get("mood")
        if mood:
            mood_counter[mood] += 1
        risk = item.get("risk")
        if isinstance(risk, (int, float)):
            risk_values.append(float(risk))

        day = (item.get("turn_ts") or item.get("ts", ""))[:10]
        triggers = item.get("triggers") or {}
        for trig, active in triggers.items():
            if active and day:
                triggers_by_day[day][trig] += 1

        for act in item.get("actions") or []:
            key = f"{act.get('device', 'unknown')}:{act.get('action', 'unknown')}"
            action_counter[key] += 1

    recent_actions = []
    for entry in data[-10:]:
        for act in entry.get("actions") or []:
            recent_actions.append(
                {
                    "ts": entry.get("ts"),
                    "device": act.get("device"),
                    "action": act.get("action"),
                    "parameters": act.get("parameters"),
                }
            )

    avg_risk = sum(risk_values) / len(risk_values) if risk_values else 0.0
    triggers_summary = {
        day: counter.most_common(5) for day, counter in triggers_by_day.items()
    }

    return {
        "total_turns": sum(1 for item in data if item.get("mood") is not None),
        "sessions_tracked": len({item.get("sid") for item in data if item.get("sid")}),
        "mood_counts": dict(mood_counter),
        "avg_risk": avg_risk,
        "recent_actions": recent_actions,
        "triggers_by_day": triggers_summary,
        "top_actions": action_counter.most_common(5),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["record_turn", "record_action", "aggregate_metrics"]
