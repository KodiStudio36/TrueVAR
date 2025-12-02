from PyQt5.QtCore import pyqtSignal, QObject
import json
import os
import glob
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
from gi.repository import Gst

from config import records_path, camera_settings_file, ai_path
from app.injector import singleton

@singleton
class CameraManager(QObject):
    is_recording_stream = pyqtSignal(bool)
    is_stream_stream = pyqtSignal(bool)

    def __init__(self):
        QObject.__init__(self)
        self.is_recording = False
        self.is_stream = False
        self.fight_num = 0

        self.is_scoreboard = True
        self.fps = 30
        self.res_width = 1280
        self.res_height = 720
        self.vaapi = True
        self.debug = True
        self.court = 1
        self.camera_idx = 0
        self.delete_records = True
        self.camera_count = 3
        self.network_ip = "192.168.0."

        self.live_camera_idx = 1
        self.live_key = ""

        self.load_cameras()
        self.get_components()

        Gst.init()

        self.shm_pipeline = None
        self.error_while_shm = False
        self.start_shmsink()

        self.segments = 0

    def get_components(self):
        self.videoconvert = "vaapipostproc" if self.vaapi else "videoconvert"
        self.videoscale = "vaapipostproc" if self.vaapi else "videoconvert ! videoscale"
        self.h264enc = "vaapih264enc" if self.vaapi else "x264enc"

    def add_camera(self):
        self.camera_count += 1
        self.save_cameras()

    def remove_camera(self):
        self.camera_count -= 1
        self.save_cameras()

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
        pipe = f"{self.get_shmsink(0)} ! video/x-raw,width=640,height=480,framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue leaky=downstream ! {self.videoscale} ! video/x-raw,width={self.res_width // 4},height={self.res_height // 4} ! tee name=overlay_tee " if self.is_scoreboard else ""

        for idx in range(1, self.camera_count + 1):
            pipe += f"{self.get_shmsink(idx)} ! video/x-raw,width={self.res_width},height={self.res_height},framerate={self.fps}/1,format=NV12,interlace-mode=progressive ! queue leaky=downstream ! {self.videoconvert}{f" ! compositor name=comp{idx+1} sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width={self.res_width},height={self.res_height}" if self.is_scoreboard else ""} ! {self.h264enc} bitrate=4000 ! avimux ! filesink location={self.get_filepath(idx, self.segments)} "
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

    def start_shmsink(self, skip_cameras=None):
        try:
            file_path = f"/tmp/camera{0}_shm_socket"
            pipe = ""

            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed: {file_path}")

            print("here", self.camera_idx)
            pipe += f"v4l2src device=/dev/video{self.camera_idx} ! image/jpeg,width=1280,height=720,framerate=30/1 ! jpegdec ! videoconvert ! video/x-raw,width=1280,height=720,framerate={self.fps}/1,format=NV12 ! capsfilter ! queue ! shmsink socket-path={file_path} wait-for-connection=false shm-size=200000000 "

            for idx in range(1, self.camera_count +1):
                file_path = f"/tmp/camera{idx}_shm_socket"

                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Removed: {file_path}")

                pipe += f"{"videotestsrc" if self.debug else self.get_camera(idx)} ! {self.videoconvert} ! video/x-raw,width={self.res_width},height={self.res_height},framerate={self.fps}/1,format=NV12 ! capsfilter ! queue ! shmsink socket-path={file_path} wait-for-connection=false shm-size=200000000 "

            print(pipe)

            if pipe != "":
                self.shm_pipeline = Gst.parse_launch(
                    pipe
                )
                bus = self.shm_pipeline.get_bus()
                bus.add_signal_watch()
                bus.connect("message", self.handle_message)
                self.shm_pipeline.set_state(Gst.State.PLAYING)

            self.error_while_shm = False
        except:
            self.error_while_shm = True

    def stop_shmsink(self):
        if self.shm_pipeline:
            self.shm_pipeline.set_state(Gst.State.NULL)

    def reload_shmsink(self):
        self.stop_shmsink()
        self.start_shmsink()

    def start_stream(self):
        self.stream_pipeline = Gst.parse_launch(
            f"{self.get_shmsink(self.live_camera_idx)} ! video/x-raw,width=1280,height=720,framerate=30/1,format=NV12,interlace-mode=progressive ! vaapipostproc ! "
            "queue ! compositor name=comp1 sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=10 sink_1::ypos=10 ! video/x-raw,width=1280,height=720 ! x264enc bitrate=2000 tune=zerolatency key-int-max=60 ! "
            f'video/x-h264,profile=main ! flvmux streamable=true name=mux ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/{self.live_key}" '
            "audiotestsrc wave=silence ! mux. "
            f"{self.get_shmsink(0)} ! video/x-raw,width=640,height=480,framerate=30/1,format=NV12,interlace-mode=progressive ! vaapipostproc ! video/x-raw,width=320,height=200 ! comp1."
        )
        self.stream_pipeline.set_state(Gst.State.PLAYING)
        self.is_stream = True
        self.is_stream_stream.emit(self.is_stream)

    def stop_stream(self):
        if self.stream_pipeline:
            self.stream_pipeline.set_state(Gst.State.NULL)
            self.is_stream = False
            self.is_stream_stream.emit(self.is_stream)

    def save_cameras(self):
        """Save camera settings to a JSON file."""
        print(self.cameras)
        data = {
            "is_scoreboard": self.is_scoreboard,
            "res_height": self.res_height,
            "debug": self.debug,
            "camera_idx": self.camera_idx,
            "live_camera_idx": self.live_camera_idx,
            "live_key": self.live_key,
            "delete_records": self.delete_records,
            "camera_count": self.camera_count,
            "court": self.court,
            "network_ip": self.network_ip,
        }

        with open(camera_settings_file, 'w') as f:
            json.dump(data, f, indent=4)

        self.get_components()

    def stop(self):
        self.stop_shmsink()
        if self.is_recording:
            self.stop_cameras()

    def load_cameras(self):
        self.cameras = []
        """Load camera settings from a JSON file."""
        if os.path.exists(camera_settings_file):
            with open(camera_settings_file, 'r') as f:
                data = json.load(f)

                self.is_scoreboard = data["is_scoreboard"]
                self.res_height = data["res_height"]
                self.res_width = self.res_height // 9 * 16
                self.debug = data["debug"]
                self.camera_idx = data["camera_idx"]
                self.live_camera_idx = data["live_camera_idx"]
                self.live_key = data["live_key"]
                self.delete_records = data["delete_records"]
                self.camera_count = data["camera_count"]
                self.court = data["court"]
                self.network_ip = data["network_ip"]

        else:
            self.save_cameras()

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
        print(self.camera_idx)
        return f"v4l2src device=/dev/video{self.camera_idx} ! video/x-raw,width=640,height=480,framerate=30/1"

    def get_camera(self, idx):
        print(f"rtspsrc location=rtsp://admin:TaekwondoVAR@{self.network_ip}{self.court}{idx}:554 latency=800 ! rtph264depay ! h264parse ! vaapih264dec")
        return f"rtspsrc location=rtsp://admin:TaekwondoVAR@{self.network_ip}{self.court}{idx}:554 latency=800 ! rtph264depay ! h264parse ! vaapih264dec"

    def get_shmsink(self, idx):
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