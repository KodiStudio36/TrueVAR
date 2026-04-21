# app/camera_manager.py
from ipaddress import ip_address

from PyQt5.QtCore import pyqtSignal, QObject, QTimer
import json
import os
import glob
import gi
import time

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GstVideo

from config import records_path, camera_settings_file, ai_path
from app.injector import singleton, Injector
from app.obs_manager import OBSManager
from app.settings_manager import SettingsManager, Setting

@singleton
class CameraManager(SettingsManager, QObject):
    is_recording_stream = pyqtSignal(bool)
    # Signal to tell ExternalScreenManager that pipeline restarted so it can move the window
    pipeline_reloaded = pyqtSignal()

    # --- Settings ---
    is_scoreboard = Setting(True)
    fps = Setting(30)
    res_height = Setting(720)
    debug = Setting(True)
    court = Setting(1)
    
    # REPLACED camera_count with camera_ips
    camera_ips = Setting(["192.168.0.11", "192.168.0.12", "192.168.0.13"]) 
    
    camera_idx = Setting(0)
    delete_records = Setting(True)
    network_ip = Setting("192.168.0.")
    live_camera_idx = Setting(1)

    auto_record = Setting(False)

    def __init__(self):
        SettingsManager.__init__(self, camera_settings_file)
        QObject.__init__(self)
        self.obs = Injector.find(OBSManager)
        
        self.is_recording = False
        self.is_stream = False
        self.fight_num = 0
        self.shm_pipeline = None
        self.error_while_shm = False
        self.segments = 0
        self.pipeline = None
        self.stream_pipeline = None

        # State to track if external screen branch should be added
        self.enable_external_screen_branch = False 
        self.window_title = "python" # Default title for xdotool/wmctrl

        if not Gst.is_initialized():
            Gst.init(None)

        self.start_shmsink()

    @property
    def camera_count(self):
        """Dynamically return the number of cameras based on the IP list."""
        return len(self.camera_ips)

    @property
    def res_width(self):
        return self.res_height // 9 * 16

    def add_camera(self):
        """Calculates the initial IP like before, but saves it to the list."""
        ips = self.camera_ips.copy()
        new_ip = f"{self.network_ip}{self.court}{len(ips) + 1}"
        ips.append(new_ip)
        self.camera_ips = ips
        
    def remove_camera(self, cam_id=None):
        """Removes a specific camera based on its index (1-based)."""
        ips = self.camera_ips.copy()
        if cam_id is None:
            # Fallback to removing the last one if no ID provided
            if len(ips) > 0:
                ips.pop()
        else:
            # cam_id is 1-based (Camera 1, Camera 2, etc.)
            if 1 <= cam_id <= len(ips):
                ips.pop(cam_id - 1)
                
        self.camera_ips = ips

    def update_camera_ip(self, idx, new_ip):
        """Updates the IP address for a specific camera."""
        if 1 <= idx <= len(self.camera_ips):
            ips = self.camera_ips.copy()
            ips[idx - 1] = new_ip
            self.camera_ips = ips

    def set_court_and_recalculate(self, court_num):
        """Updates the court and resets all camera IPs to follow the new court number."""
        self.court = court_num
        new_ips = []
        for i in range(len(self.camera_ips)):
            # idx is 1-based for the IP generation logic
            new_ips.append(f"{self.network_ip}{self.court}{i+1}")
        self.camera_ips = new_ips

    def handle_message(self, bus, message):
        msg_type = message.type
        if msg_type == Gst.MessageType.ERROR:
            err, debug_info = message.parse_error()
            print(f"Error received: {err.message} {bus}")
        elif msg_type == Gst.MessageType.EOS:
            print("End of Stream reached.")

    # --- CONTROL METHODS FOR EXTERNAL SCREEN MANAGER ---
    def set_external_screen_enabled(self, enabled: bool, window_title="python", audio_device="hw:0,0"):
        """Called by ExternalScreenManager to toggle the screen branch."""
        if self.enable_external_screen_branch != enabled:
            print(f"CameraManager: Switching External Screen to {enabled}")
            self.enable_external_screen_branch = enabled
            self.window_title = window_title
            self.audio_device = audio_device
            self.reload_shmsink()
            # Emit signal so ExternalScreenManager knows to run the 'move' script
            if enabled:
                # Give GStreamer a moment to create the window handle
                # ideally this is handled by sync_message, but for scripts, a signal works
                self.pipeline_reloaded.emit()

    # --- PIPELINE GENERATION ---
    def start_shmsink(self, skip_cameras=None):
        """
        Starts the Master Source Pipeline (Camera 0).
        If enable_external_screen_branch is True, it adds the display sink.
        """
        try:
            self.stop_shmsink()
            
            # Common Source Part (Capture -> Hardware Decode -> NV12)
            # We use 'tee' if screen is enabled, otherwise we might not strictly need it, 
            # but using it consistently is safer.
            
            try:

                file_path = f"/tmp/camera0_shm_socket"
                if os.path.exists(file_path):
                    os.remove("/tmp/camera0_shm_socket")
                    os.remove("/tmp/camera1_shm_socket")
                    os.remove("/tmp/camera2_shm_socket")
                    os.remove("/tmp/camera3_shm_socket")

            except:
                pass

            print(f"Starting Master Pipeline. Screen Enabled: {self.enable_external_screen_branch}")

            # 1. The Source and Decode
            # Note: Added 'tee name=t' at the end of the source block
            pipe_source = (
                f"{self.get_scoreboard()} "
                f"! jpegdec " 
                f"! videoconvert " 
                f"! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 "
                f"! tee name=t "
            )

            # 2. Branch A: Shared Memory (Always Active)
            pipe_shm = (
                f"t. ! queue max-size-buffers=30 max-size-bytes=0 max-size-time=0 leaky=upstream "
                f"! shmsink socket-path={file_path} wait-for-connection=false shm-size=200000000 buffer-time=0 "
            )

            # 3. Branch B: External Screen (Conditional)
            pipe_screen = ""
            if self.enable_external_screen_branch:
                # Using xvimagesink as requested. 
                # force-aspect-ratio=true helps with fullscreen stretching issues
                pipe_screen = (
                    f"t. ! queue max-size-buffers=2 max-size-bytes=0 max-size-time=0 leaky=downstream "
                    f"! xvimagesink name=extsink force-aspect-ratio=true sync=false "
                )

            full_pipe = pipe_source + pipe_shm + pipe_screen

            for idx in range(1, self.camera_count + 1):


                full_pipe += (
                    f"{"videotestsrc" if self.debug else self.get_camera(idx)} ! vapostproc "
                    f"! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! queue "
                    f"! shmsink socket-path=/tmp/camera{idx}_shm_socket wait-for-connection=false shm-size=200000000 "
                )

            print(f"Pipeline: {full_pipe}")

            self.shm_pipeline = Gst.parse_launch(full_pipe)
            bus = self.shm_pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.handle_message)
            
            # Hook for Window Title (Important for your move script)
            if self.enable_external_screen_branch:
                bus.enable_sync_message_emission()
                # bus.connect("sync-message::element", self.on_sync_message)

            self.shm_pipeline.set_state(Gst.State.PLAYING)
            self.error_while_shm = False

            QTimer.singleShot(500, self.obs.refresh_cameras)

        except Exception as e:
            print(f"Error starting Master pipeline: {e}")
            self.error_while_shm = True

    # def on_sync_message(self, bus, msg):
    #     """Sets the window title so external scripts can find it."""
    #     if not self.enable_external_screen_branch:
    #         return
            
    #     if GstVideo.is_video_overlay_prepare_window_handle_message(msg):
    #         sink = msg.src
    #         # We only care about the external screen sink
    #         if sink.get_name() == "extsink":
    #             try:
    #                 overlay = GstVideo.VideoOverlay()
    #                 # Set the title to match what ExternalScreenManager expects
    #                 overlay.set_window_title(self.window_title)
    #                 # Force a draw of the window handle
    #                 overlay.expose() 
    #             except Exception as e:
    #                 print(f"Failed to set window title: {e}")

    def stop_shmsink(self):
        if self.shm_pipeline:
            self.shm_pipeline.set_state(Gst.State.NULL)
            self.shm_pipeline = None

    def reload_shmsink(self):
        self.stop_shmsink()
        self.start_shmsink()

    # --- Other Camera Manager Methods (Recording, etc) ---
    # def get_scoreboard(self):
    #     return f"v4l2src device=/dev/video{self.camera_idx} ! image/jpeg,width=1280,height=720,framerate=30/1"

    def start_cameras(self):
        pipe = f"{self.get_shmsink(0)} ! video/x-raw,width=1280,height=720,framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue leaky=downstream ! vapostproc ! video/x-raw,width={self.res_width // 4},height={self.res_height // 4} ! tee name=overlay_tee " if self.is_scoreboard else ""

        for idx in range(1, self.camera_count + 1):
            pipe += f"{self.get_shmsink(idx)} ! video/x-raw,width={self.res_width},height={self.res_height},framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue leaky=downstream ! vapostproc{f" ! compositor name=comp{idx+1} sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width={self.res_width},height={self.res_height}" if self.is_scoreboard else ""} ! vah264enc bitrate=4000 ! avimux ! filesink location={self.get_filepath(idx, self.segments)} "
            pipe += f"overlay_tee. ! queue ! comp{idx+1}. " if self.is_scoreboard else ""

        print(pipe)

        self.pipeline = Gst.parse_launch(
            pipe
        )
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.handle_message)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.is_recording = True
        self.is_recording_stream.emit(self.is_recording)

    def stop_cameras(self):
        if self.pipeline:
            self.pipeline.send_event(Gst.Event.new_eos())
            bus = self.pipeline.get_bus()
            bus.timed_pop_filtered(Gst.SECOND, Gst.MessageType.EOS)
            self.pipeline.set_state(Gst.State.NULL)
            self.is_recording = False
            self.is_recording_stream.emit(self.is_recording)

    def stop(self):
        self.stop_shmsink()
        if self.is_recording:
            self.stop_cameras()

    def get_filepath(self, idx, segment):
        return f"{records_path}/id{self.fight_num}_camera{idx}_segment{segment}.avi"
    
    def new_segment(self):
        self.segments += 1

    def reset_segments(self):
        self.segments = 0

    def release_records(self):
        if self.delete_records:
            # Find all files in the specified directory
            files = glob.glob(os.path.join(records_path, '*'))
            
            # Iterate over each file and remove it
            for file in files:
                try:
                    os.remove(file)
                    print(f"Removed: {file}")
                except Exception as e:
                    print(f"Failed to remove {file}. Reason: {e}")

    def get_scoreboard(self):
        # Uses self.camera_idx (now a Setting)
        return f"v4l2src device=/dev/video{self.camera_idx} ! image/jpeg,width=1280,height=720,framerate=30/1"
    
    def get_camera(self, idx):
        # Uses self.network_ip, self.court (now Settings)
        ip_address = self.camera_ips[idx - 1]
        print(f"rtspsrc location=rtsp://admin:TaekwondoVAR@{ip_address}:554 latency=800 ! rtph264depay ! h264parse ! vah264dec")
        return f"rtspsrc location=rtsp://admin:TaekwondoVAR@{ip_address}:554 latency=800 ! rtph264depay ! h264parse ! vah264dec"

    def get_shmsink(self, idx):
        # Only used for idx=0 now
        return f"shmsrc socket-path=/tmp/camera{idx}_shm_socket do-timestamp=true is-live=true"

    def save_for_ai(self):
        return
        timestamp = time()
        for i in range(3):
            idx = i+1
            file_path = f"{records_path}/camera{idx}_segment1.avi"

            if os.path.exists(file_path):
                file_stats = os.stat(file_path)
                if file_stats.st_size / (1024 * 1024) < 60:
                    dst_path = f"{ai_path}/{timestamp}_{idx}.avi"
                    os.rename(file_path, dst_path)
                    print(f"Moved: {file_path} {dst_path}")