import sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import requests
from backend.inference.risk import summarize_window
from backend.inference.rag import TinyRAG

st.set_page_config(page_title="Caregiver Dashboard", page_icon="👥", layout="wide")

if "turn_scores" not in st.session_state:
    st.session_state.turn_scores = []
if "rag" not in st.session_state:
    st.session_state.rag = TinyRAG("backend/data/caregiver_guides")


st.title("👥 Caregiver Dashboard")
st.caption("Real-time insights, triggers, and gentle actions to prevent escalation.")

colA, colB = st.columns([2,1])

with colA:
    st.subheader("Trend (session)")
    if st.session_state.turn_scores:
        df = pd.DataFrame({"turn": list(range(1, len(st.session_state.turn_scores)+1)), "risk": [t["risk"] for t in st.session_state.turn_scores]})
        st.line_chart(df.set_index("turn"))
    else:
        st.info("No local data yet. Use Patient Chat or fetch from API.")

with colB:
    st.subheader("Status & Triggers (local)")
    summ = summarize_window(st.session_state.turn_scores[-5:])
    st.metric("Avg Risk (last 5)", f"{summ['risk_avg']:.2f}")
    if summ["top_triggers"]:
        st.write("**Top triggers:** " + ", ".join(summ["top_triggers"]))        
        hits = st.session_state.rag.query(" ".join(summ["top_triggers"]) + " Alzheimer agitation caregiver tips", k=3)
        st.write("**Suggested actions**")
        for h in hits:
            st.markdown(f"- **{h['title']}** — {h['snippet']}")
    else:
        st.info("No dominant triggers yet.")

st.divider()
st.subheader("API Session (optional)")
backend_url = st.text_input("Backend URL", os.getenv("BACKEND_URL", "http://localhost:8000"))
sid_in = st.text_input("Session ID (sid)", "demo1")
if st.button("Fetch from API"):
    try:
        r = requests.get(f"{backend_url}/api/session_summary", params={"sid": sid_in, "window": 5}, timeout=8)
        j = r.json()
        st.write(f"Turns: {j.get('count')} Created: {j.get('created_at')}")
        s = j.get("summary", {})
        st.metric("API Avg Risk (last 5)", f"{s.get('risk_avg', 0.0):.2f}")
        tgs = s.get("top_triggers", [])
        if tgs:
            st.write("**API Top triggers:** " + ", ".join(tgs))
        turns = j.get("turns", [])
        if turns:
            df_api = pd.DataFrame({"turn": list(range(1, len(turns)+1)), "risk": [t["risk"]["risk"] for t in turns]})
            st.line_chart(df_api.set_index("turn"))
        else:
            st.info("No turns yet for this session.")
    except Exception as e:
        st.error(f"Failed to fetch session: {e}")
