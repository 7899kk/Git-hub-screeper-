#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12+ required"'
python3 -m venv .venv-pulse
.venv-pulse/bin/python -m pip --cache-dir /workspace/.pip-cache install -r pulse_api/requirements.lock
mkdir -p data
.venv-pulse/bin/alembic -c pulse_api/alembic.ini upgrade head
.venv-pulse/bin/python -m pytest pulse_api/tests -q
.venv-pulse/bin/ruff check pulse_api
python3 -m unittest discover -s tests -q
node --check frontend/app.js
cd mobile
npm_config_cache=/workspace/.npm-cache npm ci
npm run typecheck
npm run lint
npm test
EXPO_NO_TELEMETRY=1 EXPO_OFFLINE=1 npm run build:web
EXPO_NO_TELEMETRY=1 EXPO_OFFLINE=1 npm run build:android
