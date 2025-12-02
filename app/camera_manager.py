# app/camera_manager.py
from PyQt5.QtCore import pyqtSignal, QObject
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
from app.injector import singleton
from app.settings_manager import SettingsManager, Setting

@singleton
class CameraManager(SettingsManager, QObject):
    is_recording_stream = pyqtSignal(bool)
    is_stream_stream = pyqtSignal(bool)
    # Signal to tell ExternalScreenManager that pipeline restarted so it can move the window
    pipeline_reloaded = pyqtSignal()

    # --- Settings ---
    is_scoreboard = Setting(True)
    fps = Setting(30)
    res_height = Setting(720)
    debug = Setting(True)
    court = Setting(1)
    camera_idx = Setting(0)
    delete_records = Setting(True)
    camera_count = Setting(3)
    network_ip = Setting("192.168.0.")
    live_camera_idx = Setting(1)
    live_key = Setting("")

    def __init__(self):
        SettingsManager.__init__(self, camera_settings_file)
        QObject.__init__(self)
        
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
    def res_width(self):
        return self.res_height // 9 * 16

    def add_camera(self):
        self.camera_count += 1
        self.save_settings()
        
    def remove_camera(self):
        if self.camera_count > 0:
            self.camera_count -= 1
            self.save_settings()

    def handle_message(self, bus, message):
        msg_type = message.type
        if msg_type == Gst.MessageType.ERROR:
            err, debug_info = message.parse_error()
            print(f"Error received: {err.message} {bus}")
        elif msg_type == Gst.MessageType.EOS:
            print("End of Stream reached.")

    # --- CONTROL METHODS FOR EXTERNAL SCREEN MANAGER ---
    def set_external_screen_enabled(self, enabled: bool, window_title="python"):
        """Called by ExternalScreenManager to toggle the screen branch."""
        if self.enable_external_screen_branch != enabled:
            print(f"CameraManager: Switching External Screen to {enabled}")
            self.enable_external_screen_branch = enabled
            self.window_title = window_title
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
            
            file_path = f"/tmp/camera0_shm_socket"
            if os.path.exists(file_path):
                os.remove(file_path)

            print(f"Starting Master Pipeline. Screen Enabled: {self.enable_external_screen_branch}")

            # 1. The Source and Decode
            # Note: Added 'tee name=t' at the end of the source block
            pipe_source = (
                f"{self.get_scoreboard()} "
                f"! vaapijpegdec " 
                f"! vaapipostproc " 
                f"! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 "
                f"! tee name=t "
            )

            # 2. Branch A: Shared Memory (Always Active)
            pipe_shm = (
                f"t. ! queue leaky=downstream max-size-buffers=1 "
                f"! shmsink socket-path={file_path} wait-for-connection=false shm-size=200000000 "
            )

            # 3. Branch B: External Screen (Conditional)
            pipe_screen = ""
            if self.enable_external_screen_branch:
                # Using xvimagesink as requested. 
                # force-aspect-ratio=true helps with fullscreen stretching issues
                pipe_screen = (
                    f"t. ! queue leaky=downstream max-size-buffers=1 "
                    f"! xvimagesink name=extsink force-aspect-ratio=true sync=false "
                )

            full_pipe = pipe_source + pipe_shm + pipe_screen

            for idx in range(1, self.camera_count + 1):


                full_pipe += (
                    f"{"videotestsrc" if self.debug else self.get_camera(idx)} ! vaapipostproc "
                    f"! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! queue leaky=downstream max-size-buffers=1 "
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
    def get_scoreboard(self):
        return f"v4l2src device=/dev/video{self.camera_idx} ! image/jpeg,width=1280,height=720,framerate=30/1"
    
    # def start_cameras(self):
    #     """Starts the Recording Pipeline (Scoreboard SHM + RTSP Direct)."""
        
    #     # 1. Start with the scoreboard source (SHM) and the overlay tee
    #     pipe = f"{self.get_shmsink(0)} ! video/x-raw,width=1280,height=720,framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue leaky=downstream ! vaapipostproc ! video/x-raw,width={self.res_width // 4},height={self.res_height // 4} ! tee name=overlay_tee " if self.is_scoreboard else ""

    #     # 2. Iterate through RTSP cameras (1 to N)
    #     for idx in range(1, self.camera_count + 1):
            
    #         # --- Main Pipeline for recording a single camera ---
    #         pipe += f"{self.get_shmsink(idx)} ! video/x-raw,width=1280,height=720,framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue leaky=downstream ! vaapipostproc "
            
    #         # --- Compositor and filesink ---
    #         if self.is_scoreboard:
    #             # Add compositor for the scoreboard overlay
    #             pipe += f" ! compositor name=comp{idx+1} sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width={self.res_width},height={self.res_height}"
            
    #         # Encoder and Filesink
    #         pipe += f" ! vaapih264enc bitrate=4000 ! avimux ! filesink location={self.get_filepath(idx, self.segments)} "
            
    #         # Connect the scoreboard overlay to the compositor
    #         pipe += f"overlay_tee. ! queue ! comp{idx+1}. " if self.is_scoreboard else ""

    #     print(pipe)
    #     # ... (rest of the start_cameras logic is the same)
    #     self.pipeline = Gst.parse_launch(pipe)
    #     bus = self.pipeline.get_bus()
    #     bus.add_signal_watch()
    #     bus.connect("message", self.handle_message)
    #     self.pipeline.set_state(Gst.State.PLAYING)
    #     self.is_recording = True
    #     self.is_recording_stream.emit(self.is_recording)

    def start_cameras(self):
        pipe = f"{self.get_shmsink(0)} ! video/x-raw,width=1280,height=720,framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue leaky=downstream ! vaapipostproc ! video/x-raw,width={self.res_width // 4},height={self.res_height // 4} ! tee name=overlay_tee " if self.is_scoreboard else ""

        for idx in range(1, self.camera_count + 1):
            pipe += f"{self.get_shmsink(idx)} ! video/x-raw,width={self.res_width},height={self.res_height},framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue leaky=downstream ! vaapipostproc{f" ! compositor name=comp{idx+1} sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width={self.res_width},height={self.res_height}" if self.is_scoreboard else ""} ! vaapih264enc bitrate=4000 ! avimux ! filesink location={self.get_filepath(idx, self.segments)} "
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

    # def start_shmsink(self, skip_cameras=None):
    #     """Starts the SHM Source Pipeline (ONLY for the Scoreboard/Camera 0)."""
    #     try:
    #         # 1. Scoreboard (Camera 0) logic (KEEP)
    #         file_path = f"/tmp/camera0_shm_socket"
    #         pipe = ""

    #         if os.path.exists(file_path):
    #             os.remove(file_path)
    #             print(f"Removed: {file_path}")

    #         print("Starting scoreboard shmsink:", self.camera_idx)
    #         pipe += f"{self.get_scoreboard()} ! vaapijpegdec ! queue leaky=2 max-size-buffers=1 ! vaapipostproc ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12 ! shmsink socket-path={file_path} wait-for-connection=false shm-size=200000000 "

    #         # 2. RTSP Camera Loop (REMOVED)
    #         # The loop for idx in range(1, self.camera_count + 1) is removed.
            
    #         print("SHM Sink Pipeline (Scoreboard only):", pipe)

    #         if pipe != "":
    #             self.shm_pipeline = Gst.parse_launch(pipe)
    #             bus = self.shm_pipeline.get_bus()
    #             bus.add_signal_watch()
    #             bus.connect("message", self.handle_message)
    #             self.shm_pipeline.set_state(Gst.State.PLAYING)

    #         self.error_while_shm = False
    #     except Exception as e: # Catch specific exception instead of generic
    #         print(f"Error starting SHM sink pipeline: {e}")
    #         self.error_while_shm = True

    # def stop_shmsink(self):
    #     if self.shm_pipeline:
    #         self.shm_pipeline.set_state(Gst.State.NULL)

    # def reload_shmsink(self):
    #     self.stop_shmsink()
    #     self.start_shmsink()

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