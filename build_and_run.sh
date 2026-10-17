#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"
export FLASK_APP="${FLASK_APP:-website.app}"
export FLASK_DEBUG="${FLASK_DEBUG:-0}"

PYTHON_BIN="website/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing Python environment. Create one with: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

exec "$PYTHON_BIN" -m flask run --host "${HOST:-127.0.0.1}" --port "${PORT:-5000}"
