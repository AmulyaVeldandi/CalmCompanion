# 🧠 CalmCompanion — Voice-first AI for Alzheimer’s Care

> A socially responsible AI assistant that supports **people living with Alzheimer’s** and their **caregivers** through gentle conversation, early detection of agitation, and real-time tips.

---

## ✨ Why CalmCompanion?
- Over **80% of individuals with Alzheimer’s** experience agitation at some point.  
- **70% of caregivers** report stress and burnout from managing these unpredictable episodes.  
- Technology often focuses on diagnosis — CalmCompanion instead focuses on **comfort, prevention, and support**.

---

## 🚀 Features
- **Voice-first PWA**: push-to-talk, live captions (STT), soothing responses (TTS).  
- **AI-driven detection**: analyzes speech for sentiment, agitation cues, and context.  
- **Caregiver dashboard**: clear visualization of risk trends, triggers, and suggested interventions.  
- **LLM integration (optional)**: empathetic, context-aware replies with fallback to safe heuristic rules.  
- **Privacy-first design**: no raw audio storage; all processing is session-based.  
- **Cross-platform**: works on Windows, macOS, and Linux.

---

## 🛠️ Tech Stack
- **Backend**: FastAPI, Pydantic, Uvicorn  
- **Frontend**: Streamlit (dashboard), vanilla JS PWA (voice interface)  
- **ML/NLP**: heuristics + TF-IDF retrieval (RAG) + optional LLM (Ollama or cloud)  
- **Data**: curated caregiver tips and agitation trigger taxonomy  

---

## 📂 Project Structure
```
backend/
  app.py              # FastAPI app
  core/               # settings, session store, LLM interface
  inference/          # emotion detection, risk scoring, RAG tips
frontend/
  streamlit_app.py    # main entry
  pages/              # Patient Chat & Caregiver Dashboard
voice_pwa/            # voice-first Progressive Web App
docs/                 # Model card & ethics notes
scripts/              # helper scripts for running services
```

---

## ⚡ Quickstart

### 1. Setup
```bash
git clone https://github.com/AmulyaVeldandi/CalmCompanion.git
cd CalmCompanion
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 2. Run backend
```bash
bash scripts/run_backend.sh
# or manually:
uvicorn backend.app:app --reload
```

### 3. Run dashboard
```bash
bash scripts/run_frontend.sh
# or manually:
streamlit run frontend/streamlit_app.py
```

### 4. Run voice app
```bash
bash scripts/serve_pwa.sh
# open: http://localhost:8080/index.html?api=http://localhost:8000&sid=demo1
```

---

## 🤖 Optional: LLM Integration
Enable empathetic, context-aware responses with Ollama or a cloud model.

### Local (Ollama)
```bash
ollama pull llama3.1:8b-instruct
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b-instruct
```

### Cloud
```bash
export LLM_PROVIDER=cloud
export LLM_API_KEY=sk-...
export LLM_MODEL=your-model-name
export LLM_ENDPOINT=https://api.your-llm-provider.com
```

---

## 🧭 Roadmap
- 🌅 Add time-of-day priors for sundowning episodes.  
- 🌍 Multilingual caregiver tips.  
- 📱 Native mobile + smart speaker integrations.  
- 🧪 Pilot testing with Alzheimer’s organizations.  

---

## ⚠️ Disclaimer
CalmCompanion is **assistive only**. It is not a medical device and does not provide medical advice. Caregivers should always seek professional support for health concerns.

---

✨ *Blending empathy and AI to bring calm to patients and peace of mind to caregivers.*
