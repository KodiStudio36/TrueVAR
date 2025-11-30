import os, json

from config import key_bind_settings_file
from app.injector import singleton
from app.settings_manager import SettingsManager, Setting

@singleton
class KeyBindManager(SettingsManager):
    settings_key = Setting("S")
    replay_key = Setting("R")
    record_key = Setting("N")
    next_camera_key = Setting("E")
    play_pause_key = Setting(" ")
    frame_forward_key = Setting("Right")
    frame_backward_key = Setting("Left")
    second_forward_key = Setting("Shift+Right")
    second_backward_key = Setting("Shift+Left")
    reset_zoom_key = Setting("Escape")
    toggle_external_screen_key = Setting("W")
    set_troubleshooting_scene = Setting("W")

    def __init__(self):
        super().__init__(key_bind_settings_file)
