# app/key_bind_manager.py
import os, json
from config import key_bind_settings_file

class KeyBindManager:
    def __init__(self):
        self.settings_key = "S"
        self.replay_key = "R"
        self.record_key = "N"
        self.next_camera_key = "E"
        self.play_pause_key = " "
        self.frame_forward_key = "Right"
        self.frame_backward_key = "Left"
        self.second_forward_key = "Shift+Right"
        self.second_backward_key = "Shift+Left"
        self.reset_zoom_key = "Escape"

        self.load_keybindings()

    def change_settings_key(self, new_key: str):
        self.settings_key = new_key
        self.save_keybindings()

    def change_replay_key(self, new_key: str):
        self.replay_key = new_key
        self.save_keybindings()

    def change_record_key(self, new_key: str):
        self.record_key = new_key
        self.save_keybindings()

    def change_next_camera_key(self, new_key: str):
        self.next_camera_key = new_key
        self.save_keybindings()

    def change_play_pause_key(self, new_key: str):
        self.play_pause_key = new_key
        self.save_keybindings()

    def change_frame_forward_key(self, new_key: str):
        self.frame_forward_key = new_key
        self.save_keybindings()

    def change_frame_backward_key(self, new_key: str):
        self.frame_backward_key = new_key
        self.save_keybindings()

    def change_second_forward_key(self, new_key: str):
        self.second_forward_key = new_key
        self.save_keybindings()

    def change_second_backward_key(self, new_key: str):
        self.second_backward_key = new_key
        self.save_keybindings()

    def change_reset_zoom_key(self, new_key: str):
        self.reset_zoom_key = new_key
        self.save_keybindings()

    def save_keybindings(self):
        """Save key binds to a JSON file."""
        data = {
            "settings_key": self.settings_key,
            "replay_key": self.replay_key,
            "record_key": self.record_key,
            "next_camera_key": self.next_camera_key,
            "play_pause_key": self.play_pause_key,
            "frame_forward_key": self.frame_forward_key,
            "frame_backward_key": self.frame_backward_key,
            "second_forward_key": self.second_forward_key,
            "second_backward_key": self.second_backward_key,
            "reset_zoom_key": self.reset_zoom_key,
        }
        with open(key_bind_settings_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_keybindings(self):
        """Load key binds from a JSON file."""
        if os.path.exists(key_bind_settings_file):
            with open(key_bind_settings_file, 'r') as f:
                data = json.load(f)
                self.settings_key = data["settings_key"]
                self.replay_key = data["replay_key"]
                self.record_key = data["record_key"]
                self.next_camera_key = data["next_camera_key"]
                self.play_pause_key = data["play_pause_key"]
                self.frame_forward_key = data["frame_forward_key"]
                self.frame_backward_key = data["frame_backward_key"]
                self.second_forward_key = data["second_forward_key"]
                self.second_backward_key = data["second_backward_key"]
                self.reset_zoom_key = data["reset_zoom_key"]

        else:
            self.save_keybindings()
                
