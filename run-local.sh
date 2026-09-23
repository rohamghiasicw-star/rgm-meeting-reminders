#!/bin/bash
# Local runner. Reads credentials from ~/.rgm-reminders.env (chmod 600, never in git).
cd "$(dirname "$0")" || exit 1
set -a; . "$HOME/.rgm-reminders.env" 2>/dev/null || { echo "missing ~/.rgm-reminders.env"; exit 1; }; set +a
/usr/bin/env python3 remind.py >> "$HOME/Library/Logs/rgm-reminders.log" 2>&1
