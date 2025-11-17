# app/external_screen_manager.py
import subprocess
import os
import threading
import time
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GstVideo
from PyQt5.QtCore import QObject, pyqtSignal

from app.settings_manager import SettingsManager, Setting
from app.injector import singleton
# Make sure to add 'external_screen_settings_file' to your config.py
from config import external_screen_settings_file, manage_external_screen_script

# Define path to the script. Adjust if your project structure is different.
# This assumes 'app' is one level down from the project root, and 'scripts' is also at the root.
SCRIPT_PATH = manage_external_screen_script

@singleton
class ExternalScreenManager(SettingsManager, QObject):
    """
    Manages a GStreamer pipeline for an external screen,
    controls xrandr, and moves the window to a specific workspace.
    """
    # Signal to update UI about the screen's state (running/stopped)
    screen_state_changed = pyqtSignal(bool)

    screen_changed_mirror = pyqtSignal(bool)

    # --- Settings ---
    # The 'xrandr' name for the main display (e.g., "eDP-1")
    main_display = Setting("DP-1")
    # The 'xrandr' name for the external display (e.g., "HDMI-1")
    external_display = Setting("HDMI-1")
    # The target workspace (e.g., 6)
    target_workspace = Setting(6)
    # The title the GStreamer window will have
    window_title = Setting("python")

    def __init__(self):
        # Gst.init(None) is called by CameraManager, but good practice.
        if not Gst.is_initialized():
            Gst.init(None)
        
        # Call parents' __init__
        SettingsManager.__init__(self, external_screen_settings_file)
        QObject.__init__(self)
        
        self.pipeline = None
        self.is_running = False

    def get_pipeline_string(self):
        """Constructs the GStreamer pipeline string."""
        shmsrc_socket = f"/tmp/camera0_shm_socket"
        
        # Based on CameraManager's format:
        # 'video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive'
        # We use xvimagesink as it's common and allows setting a window title.
        return (
            f"shmsrc socket-path={shmsrc_socket} do-timestamp=true is-live=true "
            f"! video/x-raw,format=NV12,width=1280,height=720,framerate=30/1 "
            f"! videoconvert "
            f"! xvimagesink name=extsink force-aspect-ratio=true"
        )

    def start_external_screen(self):
        if self.is_running:
            print("External screen is already running.")
            return
        
        if not os.path.exists(SCRIPT_PATH):
            print(f"Error: Display script not found: {SCRIPT_PATH}")
            return

        try:
            # 1. Setup xrandr to extended mode
            print(f"Setting up xrandr for {self.external_display}")
            subprocess.run([SCRIPT_PATH, "setup", self.main_display, self.external_display], check=True)
            
            # 2. Start GStreamer pipeline
            pipeline_str = self.get_pipeline_string()
            print(f"Starting GStreamer pipeline: {pipeline_str}")
            self.pipeline = Gst.parse_launch(pipeline_str)
            
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message::eos", self.on_eos)
            bus.connect("message::error", self.on_error)

            self.pipeline.set_state(Gst.State.PLAYING)
            
            # 3. In a new thread, set the window title and move it
            threading.Thread(target=self._move_window, daemon=True).start()

            self.is_running = True
            self.screen_state_changed.emit(True)

        except Exception as e:
            print(f"Failed to start external screen: {e}")
            if self.pipeline:
                self.pipeline.set_state(Gst.State.NULL)
            self.is_running = False
            self.screen_state_changed.emit(False)

    def _move_window(self):
        """(Internal) Waits for the pipeline window, sets title, and moves it."""
        try:
            # Wait for pipeline to finish transitioning to PLAYING
            self.pipeline.get_state(Gst.CLOCK_TIME_NONE)
            
            sink = self.pipeline.get_by_name("extsink")
            if not sink:
                print("Error: Could not find 'extsink' in pipeline.")
                return
                
            # Give the window time to be created by the X server
            time.sleep(1.0) 
            
            # Set the window title using the GstVideoOverlay interface
            try:
                overlay = GstVideo.VideoOverlay(sink)
                print(f"Setting window title to: {self.window_title}")
                overlay.set_window_title(self.window_title)
            except Exception as e:
                print(f"Warning: Could not get video-overlay to set window title: {e}")

            # Now, run the 'move' script
            print(f"Moving window '{self.window_title}' to workspace {self.target_workspace}")
            subprocess.run([SCRIPT_PATH, "move", self.window_title, str(self.target_workspace)])
        
        except Exception as e:
            print(f"Error in window moving thread: {e}")

    def stop_external_screen(self):
        if not self.is_running:
            print("External screen is not running.")
            return
        
        try:
            # 1. Stop GStreamer
            if self.pipeline:
                print("Stopping GStreamer pipeline.")
                self.pipeline.set_state(Gst.State.NULL)
                self.pipeline = None
            
            # 2. Reset xrandr (turn off external display)
            print(f"Resetting xrandr for {self.external_display}")
            subprocess.run([SCRIPT_PATH, "reset", self.external_display], check=True)

            self.is_running = False
            self.screen_state_changed.emit(False)

        except Exception as e:
            print(f"Error during stop: {e}")
            self.is_running = False
            self.screen_state_changed.emit(False)

    def toggle_display_mode(self):
        """Toggles between mirror and extended mode."""
        if not os.path.exists(SCRIPT_PATH):
            print(f"Error: Display script not found: {SCRIPT_PATH}")
            return
            
        print("Toggling display mode...")
        result = subprocess.run(
            [SCRIPT_PATH, "toggle", self.main_display, self.external_display],
            capture_output=True,  # Capture stdout and stderr
            text=True,            # Decode stdout and stderr as text (using the default locale encoding)
            check=False           # Don't raise an exception on non-zero exit code (optional, but safer)
        )

        self.screen_changed_mirror.emit(result.stdout == "Switching to mirror mode.\n")

    # --- GStreamer Bus Callbacks ---
    def on_eos(self, bus, msg):
        print("External screen pipeline: End-Of-Stream reached.")
        self.stop_external_screen()

    def on_error(self, bus, msg):
        err, debug = msg.parse_error()
        print(f"External screen pipeline Error: {err}, {debug}")
        self.stop_external_screen()