import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from backend.inference.emotion import analyze_text
from backend.inference.risk import score_turn
from backend.inference.rag import TinyRAG

st.set_page_config(page_title="Patient Chat", page_icon="👤", layout="wide")


if "chat" not in st.session_state:
    st.session_state.chat = []
if "turn_scores" not in st.session_state:
    st.session_state.turn_scores = []
if "rag" not in st.session_state:
    st.session_state.rag = TinyRAG("backend/data/caregiver_guides")


st.title("👤 Patient Chat (text fallback)")
st.caption("Voice PWA is primary; this page provides a text-only flow for testing.")

colL, colR = st.columns([2, 1])

with colL:
    st.subheader("Chat")
    for m in st.session_state.chat:
        st.chat_message(m.get("role", "user")).markdown(m["text"])

    msg = st.chat_input("Type a message...")
    if msg:
        st.session_state.chat.append({"role": "user", "text": msg})
        emo = analyze_text(msg)
        r = score_turn(emo["label"], emo["score"], emo["cues"], msg)
        st.session_state.turn_scores.append(r)
        reply = "Thanks for telling me. I’m here with you. Would a short break, a sip of water, or some music help?"
        st.session_state.chat.append({"role": "assistant", "text": reply})
        st.rerun()

with colR:
    st.subheader("Risk (last 5)")
    last5 = st.session_state.turn_scores[-5:]
    avg = sum(t["risk"] for t in last5)/len(last5) if last5 else 0.0
    st.progress(min(1.0, avg))
    st.write(f"**Avg risk**: {avg:.2f}")

    if st.session_state.turn_scores:
        latest = st.session_state.turn_scores[-1]
        active = [k for k, v in latest["triggers"].items() if v]
        if active:
            st.write("**Likely triggers:** " + ", ".join(active))
            q = " ".join(active) + " agitation prevention tips"
            hits = st.session_state.rag.query(q, k=2)
            st.divider()
            st.write("**Suggested actions:**")
            for h in hits:
                st.markdown(f"- **{h['title']}** — {h['snippet']}")
        else:
            st.info("No strong triggers detected yet.")
    else:
        st.info("Start chatting to see risk and tips.")

with st.expander("Demo Scripts"):
    st.markdown(
        """

**Escalating**  

> Where am I? Leave me alone!!! My head hurts and I feel lost.



**Calming**  

> I'm okay. I liked the music yesterday. Maybe a cup of tea?

"""
    )
