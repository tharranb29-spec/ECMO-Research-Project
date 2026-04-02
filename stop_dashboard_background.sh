#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$ROOT_DIR/outputs/dashboard-server.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No dashboard PID file found."
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" >/dev/null 2>&1; then
  kill "$PID"
  echo "Stopped dashboard server PID $PID"
else
  echo "Process $PID was not running."
fi

rm -f "$PID_FILE"
