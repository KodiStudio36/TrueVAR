#!/usr/bin/env bash
# Wrapper to activate venv and run main.py

cd /home/truevar/Documents/TrueVAR || exit 1

# Activate virtual environment
source /home/truevar/Documents/TrueVAR/.venv/bin/activate

# Run your script
exec python /home/truevar/Documents/TrueVAR/main.py
