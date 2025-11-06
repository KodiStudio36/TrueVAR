#!/usr/bin/env bash
# Wrapper to activate venv, optionally update repo, and run main.py

cd /home/truevar/Documents/TrueVAR || exit 1

xrandr --output HDMI-1 --mode 1920x1080 --same-as DP-1
xrandr --output HDMI-2 --mode 1920x1080 --same-as DP-1

# Check if GitHub is reachable
# if ping -c 1 github.com &> /dev/null; then
#     echo "Internet detected, updating code..."
#     git pull origin main || echo "Update failed, continuing with local code"
# else
#     echo "No internet connection, skipping update"
# fi

# Activate virtual environment
source .venv/bin/activate

# Run your script
exec python main.py
