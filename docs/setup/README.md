### Deployment Notes

- For local HTTPS, use the Compose stack in `infra/docker`.
- Systemd unit files live in `infra/systemd` and assume the project resides at `/opt/CalmCompanion`.
- Copy `.env.example` to `.env` before launching any services so docker-compose picks up required variables.
