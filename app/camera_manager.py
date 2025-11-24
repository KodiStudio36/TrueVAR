from PyQt5.QtCore import pyqtSignal, QObject
import json
import os
import glob
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
from gi.repository import Gst

# Assuming these are available in your structure
from config import records_path, camera_settings_file, ai_path
from app.injector import singleton
from app.settings_manager import SettingsManager, Setting # <--- NEW IMPORTS

@singleton
class CameraManager(SettingsManager, QObject): # <--- INHERIT FROM SettingsManager
    is_recording_stream = pyqtSignal(bool)
    is_stream_stream = pyqtSignal(bool)

    # --- Settings Definitions (Replacing instance variables) ---
    is_scoreboard = Setting(True)
    fps = Setting(30)
    res_height = Setting(720) # res_width will be a property
    debug = Setting(True)
    court = Setting(1)
    camera_idx = Setting(0) # Scoreboard camera index
    delete_records = Setting(True)
    camera_count = Setting(3) # Number of RTSP cameras (1 to N)
    network_ip = Setting("192.168.0.")
    live_camera_idx = Setting(1)
    live_key = Setting("")
    # -----------------------------------------------------------

    def __init__(self):
        # Initialize SettingsManager and load settings from file
        SettingsManager.__init__(self, camera_settings_file)
        QObject.__init__(self)
        
        # --- Internal state variables ---
        self.is_recording = False
        self.is_stream = False
        self.fight_num = 0
        self.shm_pipeline = None
        self.error_while_shm = False
        self.segments = 0
        self.pipeline = None
        self.stream_pipeline = None

        if not Gst.is_initialized():
            Gst.init(None)

        # Start the SHM source pipeline (ONLY for the scoreboard)
        self.start_shmsink()

    @property
    def res_width(self):
        """Calculates width based on the saved height."""
        return self.res_height // 9 * 16

    # Removed load_cameras and save_cameras. Use self.load_settings() / self.save_settings()

    def add_camera(self):
        self.camera_count += 1
        self.save_settings() # <--- Updated
        
    def remove_camera(self):
        if self.camera_count > 0:
            self.camera_count -= 1
            self.save_settings() # <--- Updated

    def handle_message(self, bus, message):
        """Handle messages from the GStreamer bus."""
        msg_type = message.type
        if msg_type == Gst.MessageType.ERROR:
            err, debug_info = message.parse_error()
            print(f"Error received: {err.message} {bus}")
            if debug_info:
                print(f"Debug info: {debug_info}")
            # Handle cleanup or recovery here
        elif msg_type == Gst.MessageType.WARNING:
            warn, debug_info = message.parse_warning()
            print(f"Warning received: {warn.message} {bus}")
            if debug_info:
                print(f"Debug info: {debug_info}")
        elif msg_type == Gst.MessageType.EOS:
            print("End of Stream reached.")
            # Stop the pipeline or restart if needed
        elif msg_type == Gst.MessageType.STATE_CHANGED:
            old, new, pending = message.parse_state_changed()
            print(f"Pipeline state changed from {old} to {new} {bus}")
    
    def start_cameras(self):
        """Starts the Recording Pipeline (Scoreboard SHM + RTSP Direct)."""
        
        # 1. Start with the scoreboard source (SHM) and the overlay tee
        pipe = f"{self.get_shmsink(0)} ! video/x-raw,width=1280,height=720,framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue leaky=downstream ! vaapipostproc ! video/x-raw,width={self.res_width // 4},height={self.res_height // 4} ! tee name=overlay_tee " if self.is_scoreboard else ""

        # 2. Iterate through RTSP cameras (1 to N)
        for idx in range(1, self.camera_count + 1):
            
            # --- Source: Changed from get_shmsink(idx) to get_camera(idx) ---
            source_pipe = f"{"videotestsrc" if self.debug else self.get_camera(idx)} ! vaapipostproc"
            
            # --- Main Pipeline for recording a single camera ---
            pipe += f"{source_pipe} ! video/x-raw,width={self.res_width},height={self.res_height},framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue "
            
            # --- Compositor and filesink ---
            if self.is_scoreboard:
                # Add compositor for the scoreboard overlay
                pipe += f" ! compositor name=comp{idx+1} sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width={self.res_width},height={self.res_height}"
            
            # Encoder and Filesink
            pipe += f" ! vaapih264enc bitrate=4000 ! avimux ! filesink location={self.get_filepath(idx, self.segments)} "
            
            # Connect the scoreboard overlay to the compositor
            pipe += f"overlay_tee. ! queue ! comp{idx+1}. " if self.is_scoreboard else ""

        print(pipe)
        # ... (rest of the start_cameras logic is the same)
        self.pipeline = Gst.parse_launch(pipe)
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

    def start_shmsink(self, skip_cameras=None):
        """Starts the SHM Source Pipeline (ONLY for the Scoreboard/Camera 0)."""
        try:
            # 1. Scoreboard (Camera 0) logic (KEEP)
            file_path = f"/tmp/camera0_shm_socket"
            pipe = ""

            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed: {file_path}")

            print("Starting scoreboard shmsink:", self.camera_idx)
            pipe += f"{self.get_scoreboard()} ! jpegdec ! videoconvert ! queue leaky=2 max-size-buffers=1 ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! shmsink socket-path={file_path} wait-for-connection=false shm-size=200000000 "

            # 2. RTSP Camera Loop (REMOVED)
            # The loop for idx in range(1, self.camera_count + 1) is removed.
            
            print("SHM Sink Pipeline (Scoreboard only):", pipe)

            if pipe != "":
                self.shm_pipeline = Gst.parse_launch(pipe)
                bus = self.shm_pipeline.get_bus()
                bus.add_signal_watch()
                bus.connect("message", self.handle_message)
                self.shm_pipeline.set_state(Gst.State.PLAYING)

            self.error_while_shm = False
        except Exception as e: # Catch specific exception instead of generic
            print(f"Error starting SHM sink pipeline: {e}")
            self.error_while_shm = True

    def stop_shmsink(self):
        if self.shm_pipeline:
            self.shm_pipeline.set_state(Gst.State.NULL)

    def reload_shmsink(self):
        self.stop_shmsink()
        self.start_shmsink()

    def start_stream(self):
        """Starts the Streaming Pipeline (RTSP Direct + Scoreboard SHM)."""
        
        # --- Main Stream Source: Changed from get_shmsink to get_camera ---
        stream_source = f"{"videotestsrc" if self.debug else self.get_camera(self.live_camera_idx)}"
        
        # The main pipeline starts with the RTSP source
        pipe = (
            f"{stream_source} ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! vaapipostproc ! "
            f"{self.get_shmsink(0)} ! video/x-raw,width=1280,height=720,framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! vaapipostproc ! video/x-raw,width={self.res_width // 4},height={self.res_height // 4} ! comp1."
        )

        # The compositor logic is a bit messy in your original. Cleaned up and ordered for clarity:
        pipeline_str = (
            f"{stream_source} ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! vaapipostproc ! "
            "queue ! compositor name=comp1 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! "
            f'video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/{self.live_key}" '
            "audiotestsrc wave=silence ! mux. "
            # Scoreboard Overlay: Always SHM
            f"{self.get_shmsink(0)} ! video/x-raw,width=1280,height=720,framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! vaapipostproc ! video/x-raw,width={self.res_width // 4},height={self.res_height // 4} ! comp1."
        )
        
        print("Streaming Pipeline:", pipeline_str)
        self.stream_pipeline = Gst.parse_launch(pipeline_str)
        self.stream_pipeline.set_state(Gst.State.PLAYING)
        self.is_stream = True
        self.is_stream_stream.emit(self.is_stream)

    def stop_stream(self):
        if self.stream_pipeline:
            self.stream_pipeline.set_state(Gst.State.NULL)
            self.is_stream = False
            self.is_stream_stream.emit(self.is_stream)

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
        print(f"rtspsrc location=rtsp://admin:TaekwondoVAR@{self.network_ip}{self.court}{idx}:554 latency=800 ! rtph264depay ! h264parse ! vaapih264dec")
        return f"rtspsrc location=rtsp://admin:TaekwondoVAR@{self.network_ip}{self.court}{idx}:554 latency=800 ! rtph264depay ! h264parse ! vaapih264dec"

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