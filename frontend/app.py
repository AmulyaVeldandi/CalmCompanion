from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import requests
import streamlit as st


def _normalize_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _extract_risk_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    emotion_label = None
    emotion_score = None
    risk_score = None
    risk_label = None
    triggers: List[str] = []
    plan = payload.get("plan")

    emotion = payload.get("emotion")
    if isinstance(emotion, dict):
        emotion_label = emotion.get("label") or emotion.get("name") or emotion.get("value")
        raw_score = emotion.get("score") or emotion.get("confidence")
        if isinstance(raw_score, (int, float, str)):
            try:
                emotion_score = float(raw_score)
            except (TypeError, ValueError):
                emotion_score = None
    elif isinstance(emotion, str):
        emotion_label = emotion

    risk = payload.get("risk")
    if isinstance(risk, dict):
        raw_score = (
            risk.get("score")
            or risk.get("risk")
            or risk.get("value")
            or risk.get("risk_score")
        )
        if isinstance(raw_score, (int, float, str)):
            try:
                risk_score = float(raw_score)
            except (TypeError, ValueError):
                risk_score = None
        risk_label = risk.get("label") or risk.get("level")
        if isinstance(risk.get("triggers"), list):
            triggers = [str(t) for t in risk["triggers"]]
        elif isinstance(risk.get("top_triggers"), list):
            triggers = [str(t) for t in risk["top_triggers"]]
    elif isinstance(risk, (int, float)):
        risk_score = float(risk)
    elif isinstance(risk, str):
        risk_label = risk

    # Fallbacks if data is sent under alternate keys.
    if risk_score is None:
        for key in ("risk_score", "risk_value", "riskLevel"):
            raw = payload.get(key)
            if isinstance(raw, (int, float, str)):
                try:
                    risk_score = float(raw)
                    break
                except (TypeError, ValueError):
                    continue
    if risk_label is None:
        for key in ("risk_label", "riskLevel", "status"):
            raw = payload.get(key)
            if isinstance(raw, str):
                risk_label = raw
                break

    if not triggers:
        alt_triggers = payload.get("triggers") or payload.get("top_triggers")
        if isinstance(alt_triggers, list):
            triggers = [str(t) for t in alt_triggers]

    return {
        "emotion_label": emotion_label,
        "emotion_score": emotion_score,
        "risk_score": risk_score,
        "risk_label": risk_label,
        "triggers": triggers,
        "plan": plan,
    }


def fetch_reason(base_url: str) -> Tuple[Dict[str, Any] | None, str | None]:
    url = f"{_normalize_url(base_url)}/reason"
    try:
        response = requests.get(url, timeout=6)
        if response.status_code == 405:
            # Backend might only support POST; fall back without payload.
            response = requests.post(url, json={"user_input": "status update"}, timeout=8)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data, None
        return None, "Unexpected response format from /reason."
    except requests.RequestException as exc:
        return None, f"Failed to reach /reason: {exc}"
    except ValueError as exc:
        return None, f"Invalid JSON returned by /reason: {exc}"


def trigger_calm_mode(base_url: str) -> Tuple[Dict[str, Any] | None, str | None]:
    url = f"{_normalize_url(base_url)}/smart_home"
    payload = {
        "device": "light",
        "action": "dim",
        "parameters": {"brightness": 80},
        "utterance": "Trigger calm mode",
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data, None
        return None, "Unexpected response format from /smart_home."
    except requests.RequestException as exc:
        return None, f"Failed to trigger calm mode: {exc}"
    except ValueError as exc:
        return None, f"Invalid JSON returned by /smart_home: {exc}"


def fetch_logs(base_url: str) -> Tuple[List[Dict[str, Any]], str | None]:
    url = f"{_normalize_url(base_url)}/logs"
    try:
        response = requests.get(url, timeout=6)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and isinstance(data.get("logs"), list):
            return [dict(log) for log in data["logs"]], None
        if isinstance(data, list):
            return [dict(log) if isinstance(log, dict) else {"entry": log} for log in data], None
        return [], "Unexpected response format from /logs."
    except requests.RequestException as exc:
        return [], f"Failed to fetch logs: {exc}"
    except ValueError as exc:
        return [], f"Invalid JSON returned by /logs: {exc}"


def main() -> None:
    st.set_page_config(page_title="CalmCompanion Dashboard", page_icon="🫶", layout="wide")
    st.title("Caregiver Dashboard")
    st.caption("Live caregiver signals refreshing every five seconds.")

    _ = st.autorefresh(interval=5000, limit=None, key="dashboard-autorefresh")

    with st.sidebar:
        default_backend = os.getenv("BACKEND_URL", "http://localhost:8000")
        backend_url = st.text_input("Backend URL", value=default_backend)
        st.caption("Requests: /reason, /smart_home, /logs")

    if not backend_url.strip():
        st.info("Configure a backend URL to begin.")
        return

    reason_col, calm_col = st.columns([2, 1])

    with reason_col:
        st.subheader("Real-time Emotion & Risk")
        reason_data, reason_error = fetch_reason(backend_url)
        if reason_error:
            st.error(reason_error)
        elif not reason_data:
            st.warning("No data available yet from /reason.")
        else:
            parsed = _extract_risk_fields(reason_data)
            top_row = st.columns(3)
            with top_row[0]:
                st.metric(
                    "Risk Score",
                    f"{parsed['risk_score']:.2f}" if isinstance(parsed["risk_score"], (int, float)) else "—",
                    parsed["risk_label"] or "",
                )
            with top_row[1]:
                st.metric(
                    "Emotion",
                    parsed["emotion_label"] or "—",
                    f"{parsed['emotion_score']:.2f}" if isinstance(parsed["emotion_score"], (int, float)) else "",
                )
            with top_row[2]:
                st.metric("Triggers", ", ".join(parsed["triggers"]) or "None")

            if parsed["plan"]:
                st.markdown("**Care Plan**")
                st.write(parsed["plan"])

            with st.expander("Raw /reason payload"):
                st.json(reason_data)

    with calm_col:
        st.subheader("Calm Mode")
        st.caption("Send a calming smart-home routine.")
        if st.button("Trigger Calm Mode", use_container_width=True):
            result, error = trigger_calm_mode(backend_url)
            if error:
                st.error(error)
            else:
                st.success("Calm mode triggered.")
                st.json(result)

    st.divider()
    st.subheader("System Logs")
    logs, log_error = fetch_logs(backend_url)
    if log_error:
        st.warning(log_error)
    if logs:
        st.dataframe(logs, use_container_width=True)
    elif not log_error:
        st.info("No log entries returned.")


if __name__ == "__main__":
    main()
