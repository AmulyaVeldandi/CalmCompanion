# Alexa & Smart-Home Integration Guide

CalmCompanion ships with an Alexa-compatible webhook and optional smart-home controllers (Hue, LIFX, Fire TV). Follow this guide to wire the backend into an Alexa skill and local IoT devices for your demo.

## Expose the Backend
Alexa requires a publicly reachable HTTPS endpoint with a trusted certificate.

1. Deploy the backend (see `docs/aws_deployment.md`) and front it with TLS (Caddy, API Gateway, ALB, or CloudFront).
2. Ensure the FastAPI route `/alexa` is reachable at `https://<domain>/alexa`.
3. Record the public URL; you will need it during Alexa skill configuration.
4. While prototyping, an `ngrok http 8000 --hostname=<subdomain>.ngrok.app` tunnel is acceptable, but swap to an AWS-hosted endpoint for submission.

## Create the Alexa Skill
1. Open the [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) and create a **Custom** skill.
2. Define your interaction model:
   - Add intents such as `AgitationIntent` or `ComfortIntent` with sample utterances (e.g., "Resident seems anxious").
   - Include relevant slots if you want to pass structured context; slot values appear in the skill request and are flattened by `_extract_alexa_input` (`backend/api/routers/alexa.py`). 
3. Under **Endpoint**, choose **HTTPS** and paste your public `/alexa` URL. Select the appropriate SSL certificate option (usually "My development endpoint is a sub-domain of a domain that has a wildcard certificate").
4. Save and build the model.
5. Test in the Alexa simulator. Each utterance calls the backend, which forwards the request to Bedrock via `run_reasoning_agent` and returns a rendered plan for Alexa to speak back.

### Handling Bedrock Failures
If the backend returns `502` or `500`, the skill surfaces an error. Use the `/logs` endpoint or server logs to diagnose IAM or Bedrock configuration issues.

## Smart-Home Command Endpoint
The route `POST /smart_home` accepts `DeviceCommand` payloads (see `backend/api/routers/alexa.py:232`). This allows you to execute device actions directly or from an Alexa intent handler in your skill back end.

Example payload:
```bash
curl -X POST https://<domain>/smart_home \
  -H "Content-Type: application/json" \
  -d '{
    "device": "light",
    "action": "turn_on",
    "parameters": {"brightness": 200},
    "utterance": "Dim the living room lights",
    "session_id": "demo-sid"
  }'
```
The backend sends a contextual plan to Bedrock, then invokes the appropriate controller and records the automation through `record_action` for analytics.

## Device Configuration
### Philips Hue
1. Install the optional dependency: `pip install phue`.
2. Set `HUE_BRIDGE_IP` in `.env` to the IP address of your Hue bridge.
3. Press the pairing button on the bridge and start the backend script. The controller will use group `0` (all lights) by default.

### LIFX LAN
1. Install `pip install lifxlan`.
2. No IP configuration is necessary; the library broadcasts to discover bulbs on the LAN.
3. Use the same `/smart_home` endpoint with actions `turn_on`, `turn_off`, `dim`, or `brighten`.

### Amazon Fire TV
1. Install `pip install firetv` and ensure `adb` is present.
2. Export:
   - `FIRETV_HOST` – IP of the Fire TV.
   - `FIRETV_ADB_PORT` – usually `5555`.
   - `FIRETV_ADB_KEY` – optional path to the adb key if you use authenticated pairing.
3. Trigger actions such as `play`, `pause`, `home`, and `launch` (requires `parameters.package` with the app package name).

### Testing Without Hardware
All controllers fail gracefully if dependencies or environment variables are missing; you can still demo the reasoning output by observing the JSON response and analytics events.

## Alexa + Smart-Home Flow
To combine both pieces in the demo:
1. Alexa user issues an intent ("Alexa, tell Calm Companion to prepare for bedtime").
2. Alexa sends the request to `/alexa`; the backend extracts the utterance and asks Bedrock for a plan.
3. The returned plan is used for speech, and your skill back end can also call `/smart_home` to execute automations (e.g., dimming lights) while logging analytics with `record_action`.
4. Display the resulting plan and analytics in the Streamlit dashboard for judges.

## Useful Environment Variables
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` – Bedrock access.
- `USE_BEDROCK` – ensure it remains `True` for the hackathon demo.
- `ANALYTICS_DYNAMODB_TABLE`, `ANALYTICS_S3_BUCKET` – enable remote analytics logging.
- `HUE_BRIDGE_IP`, `FIRETV_HOST`, `FIRETV_ADB_PORT`, `FIRETV_ADB_KEY` – IoT device configuration.
- `HOST`, `PORT`, `STREAMLIT_SERVER_PORT`, `PWA_PORT` – override service bindings for deployment.

Document the values you pick so teammates can replicate the setup during judging.
