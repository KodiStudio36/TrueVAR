#!/bin/bash
obs --collection "$1" &
sleep 3
# i3-msg '[class="obs"] move container to workspace 2'