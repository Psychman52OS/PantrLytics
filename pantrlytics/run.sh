#!/bin/sh
set -e

# Defaults (can be overridden by env or add-on options)
PORT="${PORT:-5000}"
WORKERS="${GUNICORN_WORKERS:-2}"

# If Home Assistant add-on options exist at /data/options.json, prefer them
if [ -f /data/options.json ]; then
  port_val=$(python - <<'PY'
import json
try:
    o=json.load(open('/data/options.json'))
    print(o.get('port',''))
except Exception:
    pass
PY
)
  workers_val=$(python - <<'PY'
import json
try:
    o=json.load(open('/data/options.json'))
    print(o.get('workers',''))
except Exception:
    pass
PY
)

  if [ -n "$port_val" ]; then
    PORT="$port_val"
  fi
  if [ -n "$workers_val" ]; then
    WORKERS="$workers_val"
  fi
fi

export PORT
export GUNICORN_WORKERS="$WORKERS"

BIND_ARGS="--bind 0.0.0.0:${PORT}"
if [ "$PORT" != "8099" ]; then
  # Also listen on 8099 so the fixed container port mapping continues to work
  BIND_ARGS="$BIND_ARGS --bind 0.0.0.0:8099"
fi

echo "[startup] Using PORT=${PORT} (bind args: ${BIND_ARGS}), GUNICORN_WORKERS=${GUNICORN_WORKERS}"

exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app ${BIND_ARGS} --workers ${GUNICORN_WORKERS} --threads 4
