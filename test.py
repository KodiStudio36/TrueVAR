import sys
import signal
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GLib

# Initialize GStreamer
Gst.init(None)

class InterpipeSystem:
    def __init__(self):
        self.mainloop = GLib.MainLoop()
        self.pipelines = []

    def create_producer(self):
        """
        Pipeline 1: The Camera Source
        - Captures video (simulated here with videotestsrc)
        - Pushes to 'interpipesink' named 'camera_node'
        """
        print("Creating Producer Pipeline...")
        pipeline_str = (
            "videotestsrc is-live=true ! "
            "video/x-raw,width=1920,height=1080,framerate=30/1 ! "
            "timeoverlay ! "  # Adds time so you can see latency differences
            "queue max-size-buffers=1 leaky=downstream ! "
            "interpipesink name=camera_node forward-events=true forward-eos=true sync=false"
        )
        return self._start_pipeline(pipeline_str, "Producer")

    def create_screen_listener(self):
        """
        Pipeline 2: The External Screen
        - Listens to 'camera_node'
        - OPTIMIZED FOR LATENCY (sync=false, small queue)
        """
        print("Creating Screen Pipeline...")
        pipeline_str = (
            "interpipesrc listen-to=camera_node is-live=true format=time ! "
            "queue max-size-buffers=1 leaky=downstream ! "
            "videoconvert ! "
            "autovideosink sync=false" # Replace with vaapisink if you have Intel drivers
        )
        return self._start_pipeline(pipeline_str, "Screen")

    def create_record_listener(self):
        """
        Pipeline 3: The Recorder
        - Listens to 'camera_node'
        - OPTIMIZED FOR QUALITY (standard queue, sync=true)
        """
        print("Creating Recording Pipeline...")
        pipeline_str = (
            "interpipesrc listen-to=camera_node is-live=true format=time ! "
            "queue max-size-buffers=1 leaky=downstream ! "
            "videoconvert ! "
            "autovideosink sync=false"
        )
        return self._start_pipeline(pipeline_str, "Recorder")

    def _start_pipeline(self, pipeline_str, name):
        pipeline = Gst.parse_launch(pipeline_str)
        
        # Bus watching for errors
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message, name)
        
        pipeline.set_state(Gst.State.PLAYING)
        self.pipelines.append(pipeline)
        return pipeline

    def on_message(self, bus, message, name):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error in {name}: {err} {debug}")
            self.shutdown()
        elif t == Gst.MessageType.EOS:
            print(f"End of Stream: {name}")

    def shutdown(self, *args):
        print("\nShutting down...")
        for p in self.pipelines:
            p.set_state(Gst.State.NULL)
        self.mainloop.quit()

    def run(self):
        # Create the independent pipelines
        self.create_producer()
        self.create_screen_listener()
        self.create_record_listener()

        # Handle Ctrl+C
        signal.signal(signal.SIGINT, self.shutdown)
        
        print("System running. Press Ctrl+C to stop.")
        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            self.shutdown()

if __name__ == "__main__":
    app = InterpipeSystem()
    app.run()