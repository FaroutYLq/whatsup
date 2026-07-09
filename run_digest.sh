#!/bin/bash
#
# ArXiv Weekly Digest Runner Script
# 
# This script runs the digest and logs output.
# Useful for cron jobs and manual runs.
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project directory
cd "$SCRIPT_DIR" || exit 1

# Find Python (try python3 first, then python)
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "Error: Python not found!"
    exit 1
fi

# Config file path
CONFIG_FILE="${1:-config.yaml}"

# Log file
LOG_FILE="$SCRIPT_DIR/digest.log"

# Run the digest
echo "======================================" | tee -a "$LOG_FILE"
echo "ArXiv Digest - $(date)" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

$PYTHON src/main.py "$CONFIG_FILE" 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

echo "" | tee -a "$LOG_FILE"
echo "Finished with exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

exit $EXIT_CODE

