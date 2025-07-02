#!/bin/bash

# This script runs the vendor updater pipeline and can be scheduled with cron

# Set working directory to the script's location
cd "$(dirname "$0")"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Log start time
echo "$(date): Starting vendor email update process" >> logs/cron.log

# Run the pipeline
python main.py >> logs/cron.log 2>&1

# Log completion
echo "$(date): Completed vendor email update process" >> logs/cron.log