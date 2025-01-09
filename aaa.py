import sys
import gi
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QMetaObject, Q_ARG
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Initialize GStreamer
Gst.init(None)

class VideoStreamWidget(QWidget):
    def __init__(self, pipeline_description, parent=None):
        super().__init__(parent)
        self.label = QLabel("Initializing video...")
        self.label.setAlignment(Qt.AlignCenter)
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Create the GStreamer pipeline with specified color format
        self.pipeline = Gst.parse_launch(pipeline_description)
        self.appsink = self.pipeline.get_by_name("sink")
        self.appsink.set_property("emit-signals", True)
        self.appsink.set_property("sync", False)
        self.appsink.connect("new-sample", self.on_new_sample)

        # Start the pipeline
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_new_sample(self, sink):
        # Callback for new samples from GStreamer pipeline
        sample = sink.emit("pull-sample")
        if sample:
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            structure = caps.get_structure(0)
            width = structure.get_value("width")
            height = structure.get_value("height")

            # Extract frame data from the buffer
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if success:
                # Ensure we are using the RGB format for PyQt compatibility
                frame_data = map_info.data
                image = QImage(frame_data, width, height, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                
                # Update the QLabel pixmap in a thread-safe way
                QMetaObject.invokeMethod(self.label, "setPixmap", Qt.QueuedConnection, Q_ARG(QPixmap, pixmap))
                
                buffer.unmap(map_info)
        return Gst.FlowReturn.OK

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multiple GStreamer AppSinks in PyQt")
        self.setGeometry(100, 100, 1280, 720)

        # Define each GStreamer pipeline for each video source
        pipelines = [
            "videotestsrc pattern=ball ! video/x-raw,format=RGB,width=360,height=640 ! queue ! videoconvert ! appsink name=sink emit-signals=True sync=True drop=False",
            "videotestsrc pattern=smpte ! video/x-raw,format=RGB,width=360,height=640 ! queue ! videoconvert ! appsink name=sink emit-signals=True sync=True drop=False",
            "v4l2src device=/dev/video0 ! video/x-raw,format=YUY2,width=640,height=480,framerate=30/1 ! queue ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink emit-signals=True sync=True drop=False"
        ]

        # Set up the layout
        layout = QHBoxLayout()

        # Create and add a VideoStreamWidget for each pipeline
        self.video_widgets = []
        for pipeline_description in pipelines:
            video_widget = VideoStreamWidget(pipeline_description)
            self.video_widgets.append(video_widget)
            layout.addWidget(video_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def closeEvent(self, event):
        # Stop all video streams on exit
        for widget in self.video_widgets:
            widget.stop()
        super().closeEvent(event)

# Run the application
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
