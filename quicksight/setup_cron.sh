#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"
MANAGE_SCRIPT="$SCRIPT_DIR/manage_schedules.py"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: config.json not found in $SCRIPT_DIR"
    exit 1
fi

EXECUTION_TIME=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['execution_time'])")
IFS=':' read -r HOUR MINUTE <<< "$EXECUTION_TIME"

echo "Setting up cron job to run at $EXECUTION_TIME (${HOUR}:${MINUTE})"

CRON_JOB="$MINUTE $HOUR * * * cd $SCRIPT_DIR && /usr/bin/python3 $MANAGE_SCRIPT"

(crontab -l 2>/dev/null | grep -v "$MANAGE_SCRIPT"; echo "$CRON_JOB") | crontab -

echo "Cron job installed successfully"
echo "Current crontab entries:"
crontab -l | grep "$MANAGE_SCRIPT"
