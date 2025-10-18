#!/usr/bin/env bash

# go to project root (folder of this script)
cd "$(dirname "$0")/.."

# activate venv
source .venv/bin/activate

python -m http.server -d voice_pwa 8080
