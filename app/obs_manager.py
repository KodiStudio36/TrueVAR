# app/obs_manager.py
from multiprocessing.forkserver import connect_to_new_process
from PyQt5.QtCore import pyqtSignal, QObject
import subprocess
import os
import time
from obswebsocket import obsws, requests, events
from app.injector import singleton
from app.settings_manager import SettingsManager, Setting
from config import obs_settings_file, launch_obs_script

@singleton
class OBSManager(SettingsManager, QObject):
    connected = pyqtSignal(bool)
    is_streaming = pyqtSignal(bool)
    scene_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    # --- Settings ---
    obs_host = Setting("localhost")
    obs_port = Setting(4455)
    obs_password = Setting("password") # Set this in your settings file or UI

    # Scene Collection Names (Must match OBS exactly)
    basic_collection_name = Setting("TrueVAR Basic Livestream")
    pro_collection_name = Setting("TrueVAR Pro Livestream")
    olympic_collection_name = Setting("TrueVAR Olympic Livestream")

    start_soon_scene = Setting("Start Soon Scene")
    main_scene = Setting("Main Scene")
    ivr_scene = Setting("IVR Scene")
    ivr_closeup_scene = Setting("IVR Closeup Scene")
    troubleshooting_scene = Setting("Troubleshooting Scene")

    def __init__(self):
        SettingsManager.__init__(self, obs_settings_file)
        QObject.__init__(self)
        self.client = None
        self.is_connected = False
        self.collection = None

    def launch_obs(self, mode="basic"):
        """
        Launches OBS Studio.
        :param mode: 'basic' or 'pro' to select the initial scene collection via CLI.
        """

        # Determine collection based on mode
        if mode == "basic":
            self.collection = self.basic_collection_name
        
        elif mode == "pro":
            self.collection = self.pro_collection_name

        elif mode == "olympic":
            self.collection = self.olympic_collection_name


        # try:
            # OBS requires the working directory to be its own bin folder usually
        subprocess.run([launch_obs_script, self.collection], check=True)
        print(f"Launching OBS with collection: {self.collection}")

        self.connect_to_obs()

        self.set_starting_scene()

            # Attempt to connect after a short delay to let OBS start
            # In a real app, you might want a retry loop in a separate thread
        # except Exception as e:
        #     self.error_occurred.emit(str(e))

    def connect_to_obs(self):
        """Establishes WebSocket connection to OBS."""
        try:
            if self.client and self.client.ws.connected:
                return

            self.client = obsws(self.obs_host, self.obs_port, self.obs_password)
            self.client.connect()
            self.is_connected = True
            self.connected.emit(True)
            print("Connected to OBS WebSocket")

        except Exception as e:
            self.is_connected = False
            self.connected.emit(False)
            print(f"Failed to connect to OBS: {e}")
            self.error_occurred.emit(f"Connection failed: {e}")

    def disconnect_obs(self):
        if self.client:
            self.client.disconnect()
            self.is_connected = False
            self.connected.emit(False)


    def set_scene(self, scene_name):
        """Switches the active Preview/Program scene."""
        if not self.is_connected: return

        try:
            self.client.call(requests.SetCurrentProgramScene(sceneName=scene_name))
            print(f"Switched to Scene: {scene_name}")
            
        except Exception as e:
            if str(e) == "socket is already closed.":
                print("here")
                self.disconnect_obs()
            print(f"Error switching scene: {e}")

    def set_starting_scene(self):
        if self.collection == self.basic_collection_name:
            self.set_scene(self.main_scene)

        elif self.collection == self.pro_collection_name or self.collection == self.olympic_collection_name:
            self.set_scene(self.start_soon_scene)

    def set_main_scene(self):
        self.set_scene(self.main_scene)

    def set_ivr_scene(self):
        if self.collection == self.pro_collection_name or self.collection == self.olympic_collection_name:
            self.set_scene(self.ivr_scene)

    def set_ivr_closeup_scene(self):
        if self.collection == self.pro_collection_name or self.collection == self.olympic_collection_name:
            self.set_scene(self.ivr_closeup_scene)

    def set_troubleshooting_scene(self):
        self.set_scene(self.troubleshooting_scene)


    def start_streaming(self):
        if not self.is_connected: self.connect_to_obs()
        try:
            self.client.call(requests.StartStream())

        except Exception as e:
            print(f"Error starting stream: {e}")

    def stop_streaming(self):
        if not self.is_connected: return
        try:
            self.client.call(requests.StopStream())
        except Exception as e:
            print(f"Error stopping stream: {e}")