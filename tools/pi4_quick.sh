#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$ROOT_DIR"

if [ -f .env ]; then
  set -a
  # shellcheck source=/dev/null
  . .env
  set +a
fi


clear_data() {
  echo "Clearing data/img and data/analyze..."
  rm -rf data/img/* data/analyze/*
}

run_option9() {
  echo "Running run_pipeline option 9 (safe → understanding → conversation)"
  printf "9
0
" | python run_pipeline.py
}

show_menu() {
  echo "Pi4 Quick Deployment"
  echo "1) Run run_pipeline option 9"
  echo "2) Clear data/img + data/analyze"
  echo "3) Run clean + option 9"
  echo "4) Show latest image / analyze file"
  echo "0) Exit"
  read -rp "Choose: " choice
  case $choice in
    1) run_option9 ;;
    2) clear_data ;;
    3) clear_data && run_option9 ;;
    4)
      ls -1 data/img | tail -n 5
      ls -1 data/analyze | tail -n 5
      ;;
    0) exit 0 ;;
    *) echo "Unknown option" ;;
  esac
}

show_menu
