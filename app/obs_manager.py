# app/obs_manager.py
from multiprocessing.forkserver import connect_to_new_process
from PyQt5.QtCore import pyqtSignal, QObject
import subprocess
import os
import time
from obswebsocket import obsws, requests, events
from app.injector import singleton, Injector
from app.main_manager import MainManager
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
    obs_password = Setting("samko211")

    kyorugi_collection_name = Setting("TrueVAR Kyorugi")
    poomsae_collection_name = Setting("TrueVAR Poomsae")

    start_soon_scene = Setting("Start Soon Scene")
    main_scene = Setting("Main Scene")
    main_scene_w_scoreboard = Setting("Main Scene \\w scoreboard")
    ivr_scene = Setting("IVR Scene")
    ivr_closeup_scene = Setting("IVR Closeup Scene")
    troubleshooting_scene = Setting("Troubleshooting Scene")

    move_transition = Setting("Move")
    stinger_transition = Setting("TrueVAR Stinger")

    def __init__(self):
        SettingsManager.__init__(self, obs_settings_file)
        QObject.__init__(self)
        self.hub = Injector.find(MainManager)

        self.client = None
        self.is_connected = False
        self.collection = None

        self.hub.start_obs_signal.connect(self.launch_obs)
        self.hub.start_livestream_signal.connect(self.start_streaming)
        self.hub.stop_livestream_signal.connect(self.stop_streaming)

    def is_obs_running(self):
        """Checks if there is an active OBS process on the system."""
        try:
            # 'pgrep -x' looks for an exact match of the process name
            subprocess.check_output(["pgrep", "-x", "obs"])
            return True
        except subprocess.CalledProcessError:
            # pgrep returns a non-zero exit code if no process is found
            return False

    def launch_obs(self, mode="kyorugi", stream_key=None):
        """
        Launches OBS Studio.
        :param mode: 'basic' or 'pro' to select the initial scene collection via CLI.
        """

        # Determine collection based on mode
        if mode == "Kyorugi DAEDO":
            self.collection = self.kyorugi_collection_name
        
        elif mode == "Poomsae FitoFan":
            self.collection = self.poomsae_collection_name

        if not self.is_obs_running():
            print(f"OBS not detected. Launching with collection: {self.collection}")
            subprocess.run([launch_obs_script, self.collection], check=True)
            print(f"Launching OBS with collection: {self.collection}")

        self.connect_to_obs()

        print("ououououououou")

        if stream_key:
            self.set_stream_key(stream_key)

        print("nououououououou")

        self.set_starting_scene()

        print("jujujujujujuj")

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

    def set_stream_key(self, stream_key):
        """Sets the OBS stream key using WebSocket v5."""
        if not self.is_connected:
            self.connect_to_obs()
            
        if not self.is_connected:
            print("Cannot set stream key: OBS not connected.")
            return

        try:
            # 1. Get current settings so we don't overwrite the Server URL/Service type
            current_settings = self.client.call(requests.GetStreamServiceSettings())
            service_type = current_settings.getStreamServiceType()
            service_settings = current_settings.getStreamServiceSettings()

            # 2. Update only the key
            service_settings["key"] = stream_key

            # 3. Push the updated settings back to OBS
            self.client.call(requests.SetStreamServiceSettings(
                streamServiceType=service_type,
                streamServiceSettings=service_settings
            ))
            print("Stream key has been successfully updated.")
            
        except Exception as e:
            print(f"Error setting stream key: {e}")
            self.error_occurred.emit(f"Failed to set stream key: {e}")

    def refresh_cameras(self):
        if self.is_obs_running() and self.client:
            source = self.client.call(requests.GetSceneItemList(sceneName="Main View  - Tool")).getSceneItems()[0]
            self.client.call(requests.SetSceneItemEnabled(
                sceneName="Main View  - Tool", 
                sceneItemId=source["sceneItemId"], 
                sceneItemEnabled=False
            ))

            time.sleep(0.1) 
            
            self.client.call(requests.SetSceneItemEnabled(
                sceneName="Main View  - Tool", 
                sceneItemId=source["sceneItemId"],
                sceneItemEnabled=True
            ))

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
            self.set_scene(self.start_soon_scene)

    def set_main_scene(self):
        self.set_scene(self.main_scene)

    def set_main_scene_w_scoreboard(self):
            self.set_scene(self.main_scene_w_scoreboard)

    def set_ivr_scene(self):
            self.set_scene(self.ivr_scene)

    def set_ivr_closeup_scene(self):
            self.set_scene(self.ivr_closeup_scene)

    def set_troubleshooting_scene(self):
        self.set_scene(self.troubleshooting_scene)

    def set_transition(self, transition_name):
        if not self.is_connected: return

        try:
            # For the newer v5 libraries (like obs-websocket-py 1.0+)
            # We use the 'SetCurrentSceneTransition' request
            self.client.call(requests.SetCurrentSceneTransition(transitionName=transition_name))
            print(f"Active transition set to: {transition_name}")
        except Exception as e:
            # If the above fails, it's likely a library attribute error
            print(f"Request failed. Check if your library supports v5: {e}")

    def set_move_transition(self):
        self.set_transition(self.move_transition)

    def set_stinger_transition(self):
        self.set_transition(self.stinger_transition)

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