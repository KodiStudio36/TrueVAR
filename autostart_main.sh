#!/usr/bin/env bash
# Wrapper to activate venv, optionally update repo, and run main.py

cd /home/truevar/Documents/TrueVAR || exit 1

xrandr --output DP-1 --auto --primary --output HDMI-2 --auto --right-of DP-1

# Check if GitHub is reachable
if ping -c 1 github.com &> /dev/null; then
    echo "Internet detected, updating code..."
    git pull origin main || echo "Update failed, continuing with local code"
else
    echo "No internet connection, skipping update"
fi

# Activate virtual environment
source .venv/bin/activate

exec pip install -r requirements.txt & python main.py
