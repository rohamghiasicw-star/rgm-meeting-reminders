#!/bin/bash
# Local runner. Credentials come from ~/.rgm-reminders.env (chmod 600, never in git).
cd "$(dirname "$0")" || exit 1
set -a; . "$HOME/.rgm-reminders.env" 2>/dev/null || { echo "missing ~/.rgm-reminders.env"; exit 1; }; set +a
PY=/opt/homebrew/bin/python3
[ -x "$PY" ] || PY=$(command -v python3)
echo "--- $(date '+%Y-%m-%d %H:%M:%S %Z') ---"
"$PY" remind.py
