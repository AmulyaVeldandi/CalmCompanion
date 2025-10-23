# CalmCompanion - Voice-first AI for Alzheimer's Care

> A socially responsible AI assistant that supports people living with Alzheimer's and their caregivers through gentle conversation, early detection of agitation, and real-time coaching.

---

## Overview
- 80%+ of individuals with Alzheimer's experience agitation, while 70% of caregivers report burnout from unpredictable episodes.
- CalmCompanion focuses on comfort, prevention, and support rather than diagnosis.
- The system pairs empathetic conversation with real-time insights, smart-home automations, and anonymized analytics.

---

## Feature Highlights
- Voice-first PWA with push-to-talk, live captions (STT), and calming TTS responses.
- Bedrock-powered reasoning plans that adapt to context and caregiver inputs.
- Risk detection pipeline (emotion analysis, heuristics, RAG tips) feeding a Streamlit dashboard.
- Optional smart-home automations (Hue, LIFX, Fire TV) and analytics sinks (DynamoDB, S3).
- Privacy-first design: conversations stay in-session; only hashed snapshots leave the device when AWS sinks are enabled.

---

## Project Structure
```text
backend/
  app.py              # FastAPI app + Alexa/smart-home routers
  api/routers/        # Alexa webhook and device command endpoints
  core/               # config, session store, LLM interfaces
  inference/          # emotion detection, risk scoring, RAG tips
  services/           # Bedrock reasoning + analytics emitters
frontend/
  streamlit_app.py    # Caregiver dashboard (risk, triggers, tips)
voice_pwa/            # Web app for live voice interactions
docs/                 # Architecture, AWS, Alexa/IoT Guides
infra/                # Docker compose + Caddy reverse proxy
scripts/runtime/      # Convenience launchers for local/AWS runs
```

---

## Quickstart (Local Development)
```bash
git clone https://github.com/AmulyaVeldandi/CalmCompanion.git
cd CalmCompanion
python -m venv .venv
source .venv/bin/activate              # Windows: .\.venv\Scripts\Activate.ps1
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env                   # edit as needed
```

Launch the services (each in its own terminal):
```bash
bash scripts/runtime/run_backend.sh    # FastAPI on http://localhost:8000
bash scripts/runtime/run_frontend.sh   # Streamlit dashboard on http://localhost:8501
bash scripts/runtime/serve_pwa.sh      # Voice PWA on http://localhost:8080
```

The scripts automatically activate `.venv` and export values from `.env`. Override ports with environment variables such as `PORT=9000` or `PWA_PORT=9001` when needed.

---

## AWS Runbook
1. **Sign in & permissions**  
   - Use an AWS region with Bedrock access.  
   - Create/attach an IAM role or user that allows `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, and optional DynamoDB/S3 write permissions.  
   - Configure AWS CLI v2 or CloudShell with those credentials.

2. **Provision compute**  
   - Launch an Amazon Linux 2023 EC2 instance (or AWS Cloud9) using the Bedrock-enabled role.  
   - Allow inbound access for the ports you intend to expose (8000, 8501, 8080) or front the instance with an ALB.

3. **Install project dependencies**  
   ```bash
   sudo dnf install -y git python3.12
   git clone https://github.com/AmulyaVeldandi/CalmCompanion.git
   cd CalmCompanion
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   cp .env.example .env
   ```

4. **Configure environment**  
   - Populate `.env` with `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, and keep `USE_BEDROCK=True`.  
   - Add optional analytics (`ANALYTICS_DYNAMODB_TABLE`, `ANALYTICS_S3_BUCKET`) or smart-home variables (`HUE_BRIDGE_IP`, `FIRETV_HOST`, etc.).  
   - For secret storage, consider SSM Parameter Store or AWS Secrets Manager instead of plain `.env` in production.

5. **Run the services**  
   ```bash
   bash scripts/runtime/run_backend.sh
   bash scripts/runtime/run_frontend.sh
   bash scripts/runtime/serve_pwa.sh
   ```
   Use `tmux`, `screen`, or systemd units to keep them alive. For containerized deployments, see `infra/docker/docker-compose.yml`.

6. **Secure public access**  
   - Terminate TLS with the provided Caddy reverse proxy (`infra/docker/caddy`) or an AWS Application Load Balancer / API Gateway.  
   - Route HTTPS traffic to the backend and dashboard, confirm `https://<domain>/reason` responds.  
   - `docs/aws_deployment.md` contains additional hosting patterns and troubleshooting tips.

7. **Smoke test Bedrock**  
   ```bash
   curl -X POST http://localhost:8000/reason \
     -H "Content-Type: application/json" \
     -d '{"user_input": "Resident is pacing near the door", "context": {"recent_risk": "high"}}'
   ```
   A plan response confirms Bedrock AgentCore is reachable; HTTP 502 usually means missing permissions or region mismatch.

---

## Alexa & Smart-Home Integration
- Expose `/alexa` over HTTPS, then create a Custom skill in the Alexa Developer Console with intents that forward to the backend. `_extract_alexa_input` flattens the request into a Bedrock prompt.  
- Optional device control uses `POST /smart_home` with payloads like `{"device": "light", "action": "turn_on"}` and records each automation through `record_action`.  
- Install optional drivers and set environment variables:  
  - Philips Hue: `pip install phue`, set `HUE_BRIDGE_IP`.  
  - LIFX LAN: `pip install lifxlan`.  
  - Fire TV: `pip install firetv`, set `FIRETV_HOST`, `FIRETV_ADB_PORT`, `FIRETV_ADB_KEY`.  
- A complete walkthrough lives in `docs/alexa_iot_setup.md`.

---

## Services & Endpoints
- `POST /reason` – Bedrock reasoning agent plan (used by PWA and Alexa).  
- `POST /api/voice_chat` – full voice turn pipeline (emotion, risk, tips, optional LLM reply).  
- `POST /smart_home` – smart-home actions + analytics logging.  
- `GET /analytics` – aggregated stats for dashboards or ML exploration.  
- `GET /logs` – recent event log entries (Bedrock calls, automations, errors).  
- `GET /api/health` – basic readiness check.

---

## Analytics & Observability
- `backend/services/analytics.py` buffers anonymized turn data and optionally emits to DynamoDB and S3.  
- `/analytics` exposes mood counts, risk averages, trigger heatmaps, and recent actions for Streamlit and the voice session UI.  
- Bedrock invocations appear in CloudWatch (region-specific); reference them in hackathon submissions to demonstrate real workloads.

---

## Optional LLM Integrations
```bash
# Ollama (local)
ollama pull llama3.1:8b-instruct
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b-instruct

# Hugging Face weights
pip install transformers torch
export LLM_PROVIDER=huggingface
export HF_MODEL_PATH=/path/to/local/model

# External cloud model
export LLM_PROVIDER=cloud
export LLM_API_KEY=sk-...
export LLM_MODEL=your-model-name
export LLM_ENDPOINT=https://api.provider.com
```
The backend prefers Bedrock when `USE_BEDROCK=True`; other providers backstop empathetic replies in `/api/voice_chat`.

---

## Docs & Resources
- `docs/aws_deployment.md` – detailed AWS deployment guide.  
- `docs/alexa_iot_setup.md` – Alexa skill + IoT configuration.  
- `docs/architecture.md` – architecture diagram and data flow notes.  
- `demo/` – sample prompts and transcripts for recorded demos.

---

## Roadmap
- Add time-of-day priors for sundowning episodes.  
- Expand multilingual caregiver tips.  
- Native mobile and smart-speaker integrations.  
- Pilot testing with Alzheimer's organizations.

---

## Disclaimer
CalmCompanion is assistive only. It is not a medical device and does not provide medical advice. Caregivers should consult professionals for health concerns.

---

*Blending empathy and AI to bring calm to patients and peace of mind to caregivers.*
