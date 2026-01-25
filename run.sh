#!/bin/bash
# Run the ambience video pipeline
# Usage: ./run.sh [concept_name]
# Example: ./run.sh "ocean waves"
# If no concept provided, picks randomly from concepts.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Log file with timestamp
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run_$(date +%Y%m%d_%H%M%S).log"

echo "Starting pipeline at $(date)" | tee "$LOG_FILE"
echo "Logging to: $LOG_FILE"

# Run the controller with optional concept argument
if [ -n "$1" ]; then
    python controller.py "$@" 2>&1 | tee -a "$LOG_FILE"
else
    python controller.py 2>&1 | tee -a "$LOG_FILE"
fi

echo "Pipeline finished at $(date)" | tee -a "$LOG_FILE"
