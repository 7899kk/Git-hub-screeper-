#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Fetch verified PyPI wheels through the current machine's supported TLS/proxy route.
# Build does not need Internet access once wheels are present.
.venv-pulse/bin/python -m pip download --only-binary=:all: --dest pulse_api/vendor -r pulse_api/requirements.lock
docker build -f pulse_api/Dockerfile -t pricepulse-api:local .
