#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

if [ -n "${UVICORN_ARGS:-}" ]; then
  # shellcheck disable=SC2206
  EXTRA_ARGS=($UVICORN_ARGS)
else
  EXTRA_ARGS=(--reload)
fi

exec uvicorn backend.app:app --host "$HOST" --port "$PORT" "${EXTRA_ARGS[@]}"
