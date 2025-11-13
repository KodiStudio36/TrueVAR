#!/bin/bash
#
# manage_display.sh (i3-specific version)
#
# Helper script to manage xrandr and i3-msg for the external screen.
#
# Usage:
#   ./manage_display.sh setup <MAIN_DISPLAY> <EXTERNAL_DISPLAY>
#   ./manage_display.sh toggle <MAIN_DISPLAY> <EXTERNAL_DISPLAY>
#   ./manage_display.sh reset <EXTERNAL_DISPLAY>
#   ./manage_display.sh move <WINDOW_TITLE> <WORKSPACE_NUM> <SCREEN_INDEX>
#

MODE="$1"

# --- Safety check for required tools ---
if ! command -v xrandr &> /dev/null; then
    echo "Error: xrandr could not be found." >&2
    exit 1
fi
if ! command -v i3-msg &> /dev/null; then
    echo "Error: i3-msg could not be found. Are you using i3?" >&2
    exit 1
fi

# --- Mode Logic ---

if [ "$MODE" == "setup" ]; then
    MAIN_DISPLAY="$2"
    EXTERNAL_DISPLAY="$3"
    
    # We rely on the i3 config for the initial monitor setup, 
    # but run a simple 'on' command just in case.
    echo "Ensuring external display $EXTERNAL_DISPLAY is enabled."
    xrandr --output "$MAIN_DISPLAY" --auto --primary --output "$EXTERNAL_DISPLAY" --auto --right-of "$MAIN_DISPLAY"

elif [ "$MODE" == "toggle" ]; then
    MAIN_DISPLAY="$2"
    EXTERNAL_DISPLAY="$3"
    
    # Check if currently mirrored by checking the external display's position.
    if xrandr | grep "$EXTERNAL_DISPLAY connected" | grep -q "+0+0"; then
        # Currently mirrored, switch to extended (use i3's definition of output placement)
        echo "Switching to extended mode (i3 config). Use 'i3-msg workspace current, move workspace to output right'."
        # This assumes your i3 config handles the extended view logic.
        # Alternatively, you can use a fixed xrandr command:
        # xrandr --output "$EXTERNAL_DISPLAY" --auto --right-of "$MAIN_DISPLAY"
        
        # NOTE: A fixed xrandr command like the commented one is often more reliable
        # than trying to infer i3's configured movement. Let's use the explicit command.
        xrandr --output "$MAIN_DISPLAY" --auto --primary --output "$EXTERNAL_DISPLAY" --auto --right-of "$MAIN_DISPLAY"
        
    else
        # Currently extended or off, switch to mirror
        echo "Switching to mirror mode."
        xrandr --output "$MAIN_DISPLAY" --auto --primary --output "$EXTERNAL_DISPLAY" --auto --same-as "$MAIN_DISPLAY"
    fi

elif [ "$MODE" == "reset" ]; then
    EXTERNAL_DISPLAY="$2"
    echo "Disabling external display: $EXTERNAL_DISPLAY"
    xrandr --output "$EXTERNAL_DISPLAY" --off

elif [ "$MODE" == "move" ]; then
    WINDOW_TITLE="$2"
    WORKSPACE_NUM="$3"
    SCREEN_INDEX="$4"
    
    echo "Looking for window with title: '$WINDOW_TITLE'"
    
    # Find the i3 window ID using i3-msg (requires jq for parsing)
    # The i3 API is complex; targeting by title is the most straightforward method.
    
    # NOTE: Since direct targeting is hard, we use i3-msg commands that affect the 
    # currently focused window, OR we use the [title="..."] selector.
    
    # 1. Target the window, move it to the specific workspace (which might be on the other screen)
    i3-msg "[title=\"$WINDOW_TITLE\"] move container to workspace $WORKSPACE_NUM"

    # 2. Move the entire workspace to the desired output/screen
    # i3 indexes outputs starting at 0 or 1. Let's assume you want to move the workspace
    # to the output defined by the screen index (which you set to 0).
    # NOTE: i3 typically uses screen names (e.g., HDMI-1) or direction (right/left)
    # to move workspaces, not numerical indices. We'll use the screen index to target the output
    # based on the order it appears in 'i3-msg -t get_outputs'.
    
    # This command uses the screen index (0) to target the output.
    # i3-msg "workspace $WORKSPACE_NUM; move workspace to output $(i3-msg -t get_outputs | jq -r --arg index "$SCREEN_INDEX" '.[$index | tonumber].name')"
    
    # 3. Make the window fullscreen on that screen
    i3-msg "[title=\"$WINDOW_TITLE\"] fullscreen toggle"

else
    echo "Usage: $0 {setup|toggle|reset|move} [args...]"
    exit 1
fi