# AWS Deployment Guide

This guide explains how to run CalmCompanion on AWS infrastructure while meeting the hackathon requirements for Bedrock-hosted reasoning and optional analytics sinks.

## Prerequisites
- AWS account with access to Amazon Bedrock in your target region.
- IAM user or role with permissions for `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`, optional DynamoDB `PutItem`, and S3 `PutObject`.
- AWS CLI v2 configured locally (`aws configure`) or an EC2/Cloud9 environment with the credentials injected.
- Python 3.12+ and git.
- (Optional) DynamoDB table and S3 bucket if you intend to persist analytics records emitted by `backend/services/analytics.py`.

## Repository Setup
```bash
git clone https://github.com/AmulyaVeldandi/CalmCompanion.git
cd CalmCompanion
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Copy the environment template and populate it with your AWS configuration:
```bash
cp .env.example .env
```

Key variables:
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` (required for Bedrock).
- `USE_BEDROCK=True` to ensure the backend uses Bedrock AgentCore for reasoning.
- `ANALYTICS_DYNAMODB_TABLE` / `ANALYTICS_S3_BUCKET` (optional analytics sinks).
- Smart-home variables such as `HUE_BRIDGE_IP`, `FIRETV_HOST`, etc. (see `docs/alexa_iot_setup.md`).

## Local Runtime Scripts
The runtime helpers automatically activate the virtual environment and load `.env`:
```bash
bash scripts/runtime/run_backend.sh      # FastAPI on :8000
bash scripts/runtime/run_frontend.sh     # Streamlit dashboard on :8501
bash scripts/runtime/serve_pwa.sh        # Voice PWA on :8080
```
Override host/port via environment variables, for example:
```bash
HOST=0.0.0.0 PORT=8000 bash scripts/runtime/run_backend.sh
STREAMLIT_SERVER_PORT=8501 bash scripts/runtime/run_frontend.sh
PWA_PORT=8080 bash scripts/runtime/serve_pwa.sh
```

## Deployment Options
### EC2 / Cloud9
1. Provision an Amazon Linux 2023 instance with an IAM role granting the Bedrock and optional DynamoDB/S3 permissions.
2. SSH into the instance, install system dependencies (`sudo dnf install git python3.12`), then follow the repository setup steps above.
3. Use `tmux` or `systemd` to run the three runtime scripts. Expose ports through a load balancer or security-group rules.

### Docker on ECS or EC2
The repo ships with a Compose stack under `infra/docker/`. Update `.env` for AWS credentials (or mount via task definitions) and deploy using ECS or a self-managed Docker host. Ensure outbound connectivity to Bedrock endpoints (VPC endpoints recommended for production).

### HTTPS Front Door
For Alexa and public demos you need TLS termination:
- Use the provided Caddy reverse proxy (`infra/docker/caddy`) or an Application Load Balancer with ACM certificates.
- Map external ports to the services: `443 -> 8000` (FastAPI) and `443 -> 8501` (Streamlit) with path-based routing.
- Confirm the public URL before recording the demo video or creating an Alexa skill endpoint.

## Observability
- The backend logs Bedrock interactions and device actions through `/logs` (`backend/event_log.py`). Access via `https://<host>/logs?limit=200`.
- Analytics snapshots push to DynamoDB and S3 when the respective environment variables are set. Validate with:
  ```bash
  aws dynamodb scan --table-name <YourTable> --max-items 3
  aws s3 ls s3://<YourBucket>/analytics/
  ```
- CloudWatch automatically captures Bedrock invocation metrics; highlight these in your submission to demonstrate real usage.

## Bedrock Checklist
- Verify `AWS_REGION` matches a Bedrock-enabled region and `BEDROCK_MODEL_ID` is available there.
- Run a smoke test:
  ```bash
  curl -X POST http://localhost:8000/reason \
    -H "Content-Type: application/json" \
    -d '{"user_input": "Resident is pacing near the door", "context": {"recent_risk": "high"}}'
  ```
- If you see `502` errors, double-check IAM permissions and network reachability to Bedrock.
