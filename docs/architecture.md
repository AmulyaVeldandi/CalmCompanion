# CalmCompanion Architecture

```mermaid
flowchart LR
    U["User"]
    ALEXA["Alexa Voice Service<br/>HTTPS"]
    FASTAPI["FastAPI Backend<br/>Port 8000"]
    BEDROCK["Bedrock AgentCore<br/>AWS API"]
    DEVICES["Smart Devices<br/>Hue / Fire TV"]
    DASH["Streamlit Dashboard<br/>Port 8501"]

    U -->|"Voice request"| ALEXA
    ALEXA -->|"REST /smart_home<br/>Port 8443 → 8000"| FASTAPI
    U -->|"Browser (PWA)<br/>Port 8443 → 8501"| DASH
    FASTAPI -->|"Inference call"| BEDROCK
    FASTAPI -->|"Device control<br/>Local integrations"| DEVICES
    FASTAPI -->|"Session analytics"| DASH
    DASH -->|"Care insights UI"| U
```

_Port 8443 is terminated by the Caddy reverse proxy, forwarding to the FastAPI backend (8000) and Streamlit dashboard (8501). Smart devices are reached on their respective local adapters._
