#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default to a repo-local data dir for local dev; HA add-on still uses /data.
export DATA_DIR="${DATA_DIR:-"$SCRIPT_DIR/data"}"
PORT="${PORT:-8099}"

cd "$SCRIPT_DIR/app"
# If you want to expose a local port during development (not under HA ingress), use 0.0.0.0:${PORT}
exec uvicorn main:app --host 0.0.0.0 --port "${PORT}"
