#!/bin/bash

# Daily Fitness Program Update Script
# This script runs the program update for all available programs

# Set the directory to the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate the virtual environment
source program_venv/bin/activate

# Create a log file with timestamp
LOG_FILE="logs/daily_update_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

# Run the program update for all programs
echo "========================================" >> "$LOG_FILE"
echo "Daily Fitness Program Update" >> "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

python3 program_update.py --program all >> "$LOG_FILE" 2>&1

# Capture the exit code
EXIT_CODE=$?

echo "========================================" >> "$LOG_FILE"
echo "Completed at: $(date)" >> "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

exit $EXIT_CODE
