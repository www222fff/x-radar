#!/bin/bash
# Usage: ./run.sh [profile]   (loads profiles/<profile>.env, default: cue)
set -e
cd "$(dirname "$0")"
PROFILE="${1:-cue}"
if [ ! -f "profiles/$PROFILE.env" ]; then
  echo "missing profiles/$PROFILE.env" >&2
  exit 1
fi
set -a
. "profiles/$PROFILE.env"
set +a
. .venv/bin/activate
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8787}"
export STORE_FILE="${STORE_FILE:-codes-$PROFILE.json}"
exec python app.py
