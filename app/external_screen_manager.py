# app/external_screen_manager.py
import subprocess
import os
import threading
import time
import gi
from PyQt5.QtCore import QObject, pyqtSignal

# Import the singleton CameraManager
from app.camera_manager import CameraManager
from app.settings_manager import SettingsManager, Setting
from app.injector import singleton, Injector
from config import external_screen_settings_file, manage_external_screen_script

SCRIPT_PATH = manage_external_screen_script

@singleton
class ExternalScreenManager(SettingsManager, QObject):
    """
    Controllers Xrandr and triggers CameraManager pipeline updates.
    Does NOT run GStreamer itself anymore.
    """
    screen_state_changed = pyqtSignal(bool)
    screen_changed_mirror = pyqtSignal(bool)

    # --- Settings ---
    main_display = Setting("DP-1")
    external_display = Setting("HDMI-1")
    target_workspace = Setting(6)
    window_title = Setting("python")
    audio_device = Setting("hw:0,0")

    def __init__(self):
        SettingsManager.__init__(self, external_screen_settings_file)
        QObject.__init__(self)
        self.is_running = False
        self.is_mirror = False
        
        # Get reference to camera manager
        self.camera_manager: CameraManager = Injector.find(CameraManager)
        
        # Connect to the signal so we know when to move the window
        self.camera_manager.pipeline_reloaded.connect(self._on_pipeline_reloaded)

    def start_external_screen(self):
        if self.is_running:
            return

        if not os.path.exists(SCRIPT_PATH):
            print(f"Error: Script not found: {SCRIPT_PATH}")
            return

        try:

            # 1. Setup Xrandr (Extended Mode)
            print(f"Setting up xrandr for {self.external_display}")
            subprocess.run([SCRIPT_PATH, "setup", self.main_display, self.external_display], check=True)
            self.is_running = True

            # 2. Tell CameraManager to include the screen branch
            # This will trigger a pipeline reload inside CameraManager
            print("Requesting CameraManager to enable screen branch...")
            self.camera_manager.set_external_screen_enabled(True, self.window_title, self.audio_device)
            
            self.screen_state_changed.emit(True)
            self.is_mirror = False
            self.screen_changed_mirror.emit(self.is_mirror)

        except Exception as e:
            print(f"Failed to enable external screen: {e}")
            self.is_running = False
            self.screen_state_changed.emit(False)

    def _on_pipeline_reloaded(self):
        print("here")
        """
        Called when CameraManager has successfully restarted with the screen branch.
        Now we can move the window.
        """
        if self.is_running:
            print("here")
            threading.Thread(target=self._move_window, daemon=True).start()

    def _move_window(self):
        """Waits briefly for X11 window creation then moves it."""
        time.sleep(1.5) # Give xvimagesink a moment to actually spawn the window
        
        print(f"Moving window '{self.window_title}' to workspace {self.target_workspace}")
        try:
            subprocess.run([SCRIPT_PATH, "move", self.window_title, str(self.target_workspace)])
        except Exception as e:
            print(f"Error moving window: {e}")

    def stop_external_screen(self):
        if not self.is_running:
            return
        
        try:
            # 1. Tell CameraManager to remove the screen branch
            print("Requesting CameraManager to disable screen branch...")
            self.camera_manager.set_external_screen_enabled(False)
            
            # 2. Reset Xrandr
            print(f"Resetting xrandr for {self.external_display}")
            subprocess.run([SCRIPT_PATH, "reset", self.external_display], check=True)

            self.is_running = False
            self.screen_state_changed.emit(False)
            self.is_mirror = False
            self.screen_changed_mirror.emit(self.is_mirror)

        except Exception as e:
            print(f"Error stopping external screen: {e}")

    def toggle_display_mode(self):
        # (This remains mostly the same, handling xrandr toggles)
        if not self.is_running or not os.path.exists(SCRIPT_PATH):
            return
        result = subprocess.run(
            [SCRIPT_PATH, "toggle", self.main_display, self.external_display],
            capture_output=True, text=True, check=False
        )
        self.is_mirror = result.stdout == "Switching to mirror mode.\n"
        self.screen_changed_mirror.emit(self.is_mirror)