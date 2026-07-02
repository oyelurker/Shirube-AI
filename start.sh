#!/usr/bin/env bash
# Boot the Shirube AI FastAPI server. Run from the backend working directory
# so that `agents.*` imports resolve. Honors Cloud Run's $PORT (default 8080).
set -euo pipefail

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}"
