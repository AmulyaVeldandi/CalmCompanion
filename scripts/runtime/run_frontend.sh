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

HOST="${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}"
PORT="${STREAMLIT_SERVER_PORT:-8501}"

EXTRA_ARGS=()
if [ -n "${STREAMLIT_ARGS:-}" ]; then
  # shellcheck disable=SC2206
  EXTRA_ARGS=($STREAMLIT_ARGS)
fi

exec streamlit run frontend/streamlit_app.py --server.address "$HOST" --server.port "$PORT" "${EXTRA_ARGS[@]}"
