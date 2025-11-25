#!/bin/sh
set -e

# Defaults (can be overridden by env or add-on options)
PORT="${PORT:-8099}"
WORKERS="${GUNICORN_WORKERS:-2}"

# If Home Assistant add-on options exist at /data/options.json, prefer workers only
if [ -f /data/options.json ]; then
  workers_val=$(python - <<'PY'
import json
try:
    o=json.load(open('/data/options.json'))
    print(o.get('workers',''))
except Exception:
    pass
PY
)
  if [ -n "$workers_val" ]; then
    WORKERS="$workers_val"
  fi
fi

export PORT
export GUNICORN_WORKERS="$WORKERS"

BIND_ARGS="--bind 0.0.0.0:${PORT}"
echo "[startup] Using container PORT=${PORT} (bind args: ${BIND_ARGS}), GUNICORN_WORKERS=${GUNICORN_WORKERS}"
echo "[startup] Reminder: configure the host port in the HA add-on Network tab (container always listens on 8099 internally)."

exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app ${BIND_ARGS} --workers ${GUNICORN_WORKERS} --threads 4
