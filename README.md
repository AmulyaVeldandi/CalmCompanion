# CalmCompanion — Voice-first AI for Alzheimer’s Care

CalmCompanion is a voice-first assistant that supports people living with Alzheimer’s and their caregivers. It detects early signs of agitation from conversation, offers calming replies for the patient, and surfaces real-time triggers and tips for the caregiver.

> **Assistive only** — This project is not a medical device and does not provide medical advice.

## Features
- **Voice-first PWA** (mobile web) with push-to-talk, captions (STT), and TTS replies.
- **FastAPI backend** with in-memory sessions, risk scoring, trigger detection, and local RAG tips.
- **Streamlit caregiver dashboard** for trends, triggers, and an explainable “why-panel”.
- **Privacy-first demo**: local processing; no raw audio stored.

## Quickstart

### 1) Install Python deps
```bash
python3 -m venv .venv
source .venv/bin/activate                  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

### 2) Start backend
```bash
uvicorn backend.app:app --reload
# http://127.0.0.1:8000/docs
```

### 3) Open Voice PWA
Serve the `voice_pwa/` directory or open directly in your browser:
```
python -m http.server -d voice_pwa 8080
# Visit: http://localhost:8080/index.html?api=http://localhost:8000&sid=demo1
```

### 4) Open Caregiver Dashboard (Streamlit)
```bash
streamlit run frontend/streamlit_app.py
# In Dashboard → API Session: enter backend URL and sid (e.g., demo1)
```

## Project Structure
```
backend/
  app.py                 # FastAPI app, routes, CORS, sessions
  core/
    config.py            # settings
    session_store.py     # in-memory session store (extensible)
  inference/
    emotion.py           # lexicon sentiment + agitation cue extraction
    risk.py              # risk scoring, triggers, time-of-day prior, summarize
    rag.py               # tiny TF-IDF retrieval over caregiver tips
  data/caregiver_guides/tips.md
frontend/
  streamlit_app.py       # launcher
  pages/
    1_Patient_Chat.py
    2_Caregiver_Dashboard.py
voice_pwa/
  index.html             # voice UI (Web Speech API STT/TTS)
  app.js
  style.css
docs/
  MODEL_CARD.md
  PRIVACY_ETHICS.md
```

## Rubric Alignment
- **Impact**: Early warning and de-escalation for Alzheimer’s agitation; supports both patient and caregiver.
- **UI**: Voice-first PWA with large controls; simple, high-contrast; dashboard with clear trends and tips.
- **Code Documentation**: Clear naming, docstrings, comments, and docs in `docs/`.
- **Relevance to Theme**: Directly addresses social impact (elder care, caregiver burden) with responsible AI.
- **State of Project**: Both **frontend** and **backend** complete and runnable.
- **Age of Code**: Freshly generated for this hackathon.

## Commands (shortcuts)
```bash
bash scripts/run_backend.sh
bash scripts/run_frontend.sh
bash scripts/serve_pwa.sh
```

