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
  api/routers/        # Alexa + smart home endpoints
  core/               # settings, session store, LLM interface
  inference/          # emotion detection, risk scoring, RAG tips
  services/           # Bedrock agent + analytics sink
frontend/
  streamlit_app.py    # main entry
  pages/              # Patient Chat & Caregiver Dashboard
voice_pwa/            # voice-first Progressive Web App
demo/
  prompts/            # Persona + reasoning prompts
  sample_transcripts/ # Longer narrative transcripts
  scripts/            # End-to-end demo flows
docs/                 # Model card & ethics notes
infra/
  docker/             # Compose stack + Caddy reverse proxy
  systemd/            # Unit files for Linux services
scripts/
  runtime/            # Convenience wrappers for local dev
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
bash scripts/runtime/run_backend.sh
# or manually:
uvicorn backend.app:app --reload
```

### 3. Run dashboard
```bash
bash scripts/runtime/run_frontend.sh
# or manually:
streamlit run frontend/streamlit_app.py
```

### 4. Run voice app
```bash
bash scripts/runtime/serve_pwa.sh
# open: http://localhost:8080/index.html?api=http://localhost:8000&sid=demo1
```

### 5. Configure environment variables
```bash
cp .env.example .env
```
Update the copied file with your AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`), toggle advanced features (`USE_BEDROCK`, `USE_LOCAL_SPEECH`), point analytics to AWS services if desired (`ANALYTICS_DYNAMODB_TABLE`, `ANALYTICS_S3_BUCKET`), and set LLM options (`LLM_PROVIDER`, `LLM_MODEL`, `HF_MODEL_PATH` for local Hugging Face weights).

---

## 🔒 Local HTTPS with Caddy
Docker Compose now includes a Caddy reverse proxy that terminates TLS with a self-signed (internal CA) certificate.

- Start everything: `docker compose -f infra/docker/docker-compose.yml up`
- Trust the generated certificate (one-time): `docker compose -f infra/docker/docker-compose.yml exec caddy caddy trust`
- Backend APIs (`/reason`, `/analytics`, `/smart_home`, `/api/*`) are available at `https://localhost:8443`
- Streamlit dashboard: `https://localhost:8443/dashboard/`
- Voice PWA: `https://localhost:8443/voice/`

If you already rely on another reverse proxy, disable the `caddy` service and reuse the backend ports (8000/8501/8080).

## 📊 Analytics Pipeline
- `backend/services/analytics.py` stores anonymized turn context, mood detection, and smart-home actions.
- Aggregated insights (mood counts, trigger heatmaps, recent automations) are exposed via `/analytics` for dashboards or SageMaker notebooks.
- Configure AWS sinks through `.env` (`ANALYTICS_DYNAMODB_TABLE`, `ANALYTICS_S3_BUCKET`). Without credentials, the collector uses in-memory storage only.
- Sample Bedrock persona prompt is available in `demo/prompts/soothing_agent.txt`.

## 🎬 Demo the full flow
Run `python demo/scripts/full_flow.py` (or execute the shebang directly) to:
1. Send “user feeling anxious” to `/reason` and print the plan.
2. Dim the lights and launch a Fire TV relaxation video via `/smart_home`.
3. Fetch `/analytics` to preview aggregated metrics.

Set `CALMCOMP_BASE_URL` to target a remote stack. For self-signed TLS, either trust the Caddy certificate or keep `CALMCOMP_VERIFY_SSL=false` in your environment.

## 🖥️ Systemd deployment (Ubuntu/Debian)
1. Place the project under `/opt/CalmCompanion` (adjust the path if you choose a different location).
2. Copy the unit file: `sudo cp infra/systemd/calmcompanion.service /etc/systemd/system/`
3. Update `WorkingDirectory` and compose path inside the unit to your project path.
4. Reload and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now calmcompanion
   ```
5. Inspect status/logs: `systemctl status calmcompanion`, `journalctl -u calmcompanion -f`

The unit keeps `docker compose -f infra/docker/docker-compose.yml up` running in the foreground so a crash restarts the stack (`Restart=on-failure`).

---

## 🤖 Optional: LLM Integration
Enable empathetic, context-aware responses with Ollama, locally downloaded Hugging Face weights, or a cloud model.

### Local (Ollama)
```bash
ollama pull llama3.1:8b-instruct
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b-instruct
```

### Local (Hugging Face weights)
```bash
pip install transformers torch  # choose the correct torch wheel for your platform
export LLM_PROVIDER=huggingface
export HF_MODEL_PATH=/path/to/downloaded/model  # e.g. ~/models/Mistral-7B-Instruct
# or point LLM_MODEL to a local repository name via `huggingface-cli download`
```
The backend loads weights with `local_files_only=True`, so models must be present in the local Hugging Face cache or directory.

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
