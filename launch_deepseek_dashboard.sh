#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "ECMO dashboard launcher"
echo

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

echo
echo "Refreshing model outputs..."
python3 ecmo_seed_ranker.py
python3 build_dashboard_bundle.py

echo
echo "Starting live dashboard server..."
echo "Open http://127.0.0.1:8765/dashboard.html in your browser"
echo "Press Ctrl+C in this terminal to stop the server"
echo

python3 research_assistant_server.py
