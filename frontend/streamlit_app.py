import sys
from pathlib import Path

# Ensure repo root is importable (works regardless of cwd)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(page_title="CalmCompanion", page_icon="🫶", layout="wide")
st.title("CalmCompanion — Voice-first AI for Alzheimer’s Care")
st.write("Use the sidebar to open **Patient Chat** or **Caregiver Dashboard**.")
st.caption("Assistive demo — not a medical device and not medical advice.")
