#!/usr/bin/env python3

"""
Demonstrate the CalmCompanion reasoning and smart home flow from the CLI.

Steps:
1. Sends a caregiving concern to the Bedrock reasoning endpoint.
2. Prints the generated plan.
3. Issues smart home commands to dim the lights and launch a relaxation video.
4. Displays a snapshot of aggregated analytics.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import requests
import urllib3


def _bool_from_env(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def post_json(url: str, payload: Dict[str, Any], verify: bool) -> requests.Response:
    try:
        return requests.post(url, json=payload, timeout=15, verify=verify)
    except requests.RequestException as exc:
        raise SystemExit(f"Request to {url} failed: {exc}")


def get_json(url: str, verify: bool) -> Dict[str, Any]:
    try:
        response = requests.get(url, timeout=15, verify=verify)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise SystemExit(f"Request to {url} failed: {exc}")


def main() -> None:
    base_url = os.getenv("CALMCOMP_BASE_URL", "https://localhost:8443")
    verify_ssl = _bool_from_env(os.getenv("CALMCOMP_VERIFY_SSL"), default=False)
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    message = "user feeling anxious"
    print(f"[1/4] Sending concern to /reason: {message!r}")
    reason_resp = post_json(f"{base_url}/reason", {"user_input": message}, verify=verify_ssl)
    try:
        reason_resp.raise_for_status()
        plan = reason_resp.json().get("plan", "(no plan returned)")
    except (ValueError, requests.HTTPError):
        print("Failed to decode /reason response:", reason_resp.text)
        sys.exit(1)

    print("[2/4] Reasoning plan from Bedrock:")
    print("-" * 60)
    print(plan)
    print("-" * 60)

    commands: List[Dict[str, Any]] = [
        {
            "device": "light",
            "action": "dim",
            "parameters": {"brightness": 80},
            "utterance": "Please dim the lights; the caregiver needs a gentler ambience.",
            "session_id": "demo-script",
        },
        {
            "device": "firetv",
            "action": "launch",
            "parameters": {
                "package": os.getenv("CALMCOMP_FIRETV_RELAX_APP", "com.amazon.tv.relaxation"),
                "content": "FireTV relaxation video",
            },
            "utterance": "Play a relaxation video on Fire TV.",
            "session_id": "demo-script",
        },
    ]

    for idx, command in enumerate(commands, start=3):
        description = f"[{idx}/4] Calling /smart_home for {command['device']} -> {command['action']}"
        print(description)
        resp = post_json(f"{base_url}/smart_home", command, verify=verify_ssl)
        if resp.status_code == 200:
            payload = resp.json()
            execution = payload.get("execution", {})
            print(f"  ✓ plan snippet: {payload.get('plan', '')[:80]}...")
            print(f"  ✓ execution: {json.dumps(execution, indent=2)}")
        else:
            print(f"  ⚠ request failed ({resp.status_code}): {resp.text}")

    print("[4/4] Fetching aggregated analytics from /analytics")
    analytics = get_json(f"{base_url}/analytics", verify=verify_ssl)
    highlights = {
        "total_turns": analytics.get("total_turns"),
        "avg_risk": analytics.get("avg_risk"),
        "mood_counts": analytics.get("mood_counts"),
        "triggers_by_day": analytics.get("triggers_by_day"),
        "top_actions": analytics.get("top_actions"),
    }
    print(json.dumps(highlights, indent=2))


if __name__ == "__main__":
    main()
