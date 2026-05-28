#!/bin/bash

echo "QuickSight Schedule Manager - Initialization"
echo "============================================="
echo ""

# Check if config.json has datasets
DATASET_COUNT=$(python3 -c "import json; c=json.load(open('config.json')); print(len(c.get('datasets', {})))" 2>/dev/null || echo "0")

if [ "$DATASET_COUNT" -eq 0 ]; then
    echo "No datasets found in config.json"
    echo ""
    echo "Running init_config.py to auto-discover datasets..."
    python3 init_config.py
else
    echo "Found $DATASET_COUNT datasets in config.json"
fi

echo ""
echo "Next steps:"
echo "1. Review config.json and set auto_enable: true for datasets you want to manage"
echo "2. Run: python3 list_schedules.py (to view current schedules)"
echo "3. Run: python3 manage_schedules.py (to test enable/disable logic)"
echo "4. Run: bash setup_cron.sh (to install daily cron job)"
echo ""
echo "Documentation:"
echo "- QUICKSTART.md - Quick 5-minute setup guide"
echo "- README.md - Full technical documentation"
echo "- PROJECT_SUMMARY.md - Architecture and overview"
