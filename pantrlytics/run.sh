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

echo "[startup] Using PORT=${PORT}, GUNICORN_WORKERS=${GUNICORN_WORKERS}"

exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS} --threads 4
