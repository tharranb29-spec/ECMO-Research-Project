#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$ROOT_DIR/outputs/dashboard-server.pid"
LOG_FILE="$ROOT_DIR/outputs/dashboard-server.log"

mkdir -p "$ROOT_DIR/outputs"
cd "$ROOT_DIR"

if [[ -f "$PID_FILE" ]]; then
  EXISTING_PID="$(cat "$PID_FILE")"
  if kill -0 "$EXISTING_PID" >/dev/null 2>&1; then
    echo "Dashboard server already running with PID $EXISTING_PID"
    echo "Open http://127.0.0.1:8765/dashboard.html"
    exit 0
  fi
fi

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  printf "Enter your DeepSeek API key: "
  read DEEPSEEK_API_KEY
fi

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DeepSeek API key was empty. Exiting."
  exit 1
fi

export AI_PROVIDER="deepseek"
export DEEPSEEK_API_KEY
export DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-chat}"
export AUTO_RESEARCH_ENABLED="${AUTO_RESEARCH_ENABLED:-1}"
export AUTO_RESEARCH_INTERVAL_SECONDS="${AUTO_RESEARCH_INTERVAL_SECONDS:-3600}"
export AUTO_RESEARCH_LLM_ENABLED="${AUTO_RESEARCH_LLM_ENABLED:-1}"

python3 ecmo_seed_ranker.py
python3 build_dashboard_bundle.py

nohup python3 research_assistant_server.py >"$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" >"$PID_FILE"

echo "Dashboard server started in background with PID $SERVER_PID"
echo "Log file: $LOG_FILE"
echo "Open http://127.0.0.1:8765/dashboard.html"
