from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTabWidget, QScrollArea, QFrame, QDialog, QCheckBox,
    QStyle, QSizePolicy, QKeySequenceEdit, QFormLayout
)
import gi
from PyQt5.QtGui import QPixmap, QIcon, QFont, QImage
from PyQt5.QtCore import Qt, QMetaObject, Q_ARG
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import cv2
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QApplication
)
from cv2_enumerate_cameras import enumerate_cameras

class AddCameraDialog(QDialog):
    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Add Camera")
        layout = QVBoxLayout()

        # Camera selection combo box
        self.camera_selector = QComboBox(self)
        self.camera_selector.addItem("Other")  # Option to add a custom camera
        self.cameras = self.detect_cameras()
        
        # Populate combo box with detected cameras
        for cam in self.cameras:
            self.camera_selector.addItem(f"Camera {cam['index']}")
        
        self.camera_selector.currentIndexChanged.connect(self.populate_camera_info)

        self.new_cam_resolution = QLineEdit(self)
        self.new_cam_resolution.setPlaceholderText("Resolution (width, height)")

        self.new_cam_fps = QLineEdit(self)
        self.new_cam_fps.setPlaceholderText("FPS")

        self.new_cam_format = QLineEdit(self)
        self.new_cam_format.setPlaceholderText("Format (e.g., MJPG)")

        self.new_cam_gstreamer_src = QLineEdit(self)
        self.new_cam_gstreamer_src.setPlaceholderText("GStreamer Source")

        # Add Camera button
        add_cam_button = QPushButton("Add Camera")
        add_cam_button.clicked.connect(self.add_camera)

        # Layout widgets
        layout.addWidget(QLabel("Select Camera"))
        layout.addWidget(self.camera_selector)
        layout.addWidget(self.new_cam_resolution)
        layout.addWidget(self.new_cam_fps)
        layout.addWidget(self.new_cam_format)
        layout.addWidget(self.new_cam_gstreamer_src)
        layout.addWidget(add_cam_button)
        
        self.setLayout(layout)

    def detect_cameras(self):
        cameras = []
        for camera_info in enumerate_cameras(cv2.CAP_GSTREAMER):
            camera = cv2.VideoCapture(camera_info.index)
            if camera.isOpened():
                width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(camera.get(cv2.CAP_PROP_FPS))
                fourcc = int(camera.get(cv2.CAP_PROP_FOURCC))
                print(fourcc)
                format = (
                    chr((fourcc & 0xFF)) +
                    chr((fourcc >> 8) & 0xFF) +
                    chr((fourcc >> 16) & 0xFF) +
                    chr((fourcc >> 24) & 0xFF)
                )

                if format == "YUYV" : format = "YUY2"

                cameras.append({
                    "index": camera_info.index,
                    "resolution": (width, height),
                    "fps": fps,
                    "format": format,
                    "gstreamer_src": f"v4l2src device={camera_info.path}"
                })
            camera.release()
        return cameras

    def populate_camera_info(self):
        selected_index = self.camera_selector.currentIndex() - 1
        if selected_index >= 0:
            # Populate with camera information
            camera_info = self.cameras[selected_index]
            self.new_cam_resolution.setText(f"{camera_info['resolution'][0]}, {camera_info['resolution'][1]}")
            self.new_cam_fps.setText(str(camera_info['fps']))
            self.new_cam_format.setText(camera_info['format'])
            self.new_cam_gstreamer_src.setText(str(camera_info['gstreamer_src']))
        else:
            # Clear fields for "Other" selection
            self.new_cam_resolution.clear()
            self.new_cam_fps.clear()
            self.new_cam_format.clear()
            self.new_cam_gstreamer_src.clear()

    def add_camera(self):
        resolution = tuple(map(int, self.new_cam_resolution.text().split(','))) if self.new_cam_resolution.text() else (640, 480)
        fps = int(self.new_cam_fps.text()) if self.new_cam_fps.text() else 30
        format = self.new_cam_format.text()
        gstreamer_src = self.new_cam_gstreamer_src.text()

        # Add camera to camera manager with provided settings
        self.camera_manager.add_camera(resolution=resolution, fps=fps, format=format, device=gstreamer_src)
        self.accept()  # Close the dialog


class VideoStreamWidget(QWidget):
    def __init__(self, pipeline_description, parent=None):
        super().__init__(parent)
        self.pipeline_description = pipeline_description
        self.label = QLabel("Initializing video...")
        self.label.setFixedSize(272, 153)
        self.label.setAlignment(Qt.AlignCenter)
        self.pipeline = None
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def start(self):
        # Create the GStreamer pipeline with specified color format
        self.pipeline = Gst.parse_launch(self.pipeline_description)
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
                image = QImage(frame_data, 272, 153, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                
                # Update the QLabel pixmap in a thread-safe way
                QMetaObject.invokeMethod(self.label, "setPixmap", Qt.QueuedConnection, Q_ARG(QPixmap, pixmap))
                
                buffer.unmap(map_info)
        return Gst.FlowReturn.OK

    def stop(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)

class SettingsScreen(QWidget):
    def __init__(self, key_bind_manager, camera_manager):
        super().__init__()
        self.key_bind_manager = key_bind_manager
        self.camera_manager = camera_manager
        self.video_widgets = []
        self.init_ui()

    def init_ui(self):
        # Main layout with tabs
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding around the tab widget
        self.tabs = QTabWidget()
        self.tabs.setContentsMargins(0, 0, 0, 0)  # Remove padding inside the tab

        # Camera Settings Tab
        self.init_tabs()
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def init_tabs(self):
        self.camera_settings_tab = QWidget()
        self.init_camera_settings_tab()
        self.tabs.addTab(self.camera_settings_tab, "Camera Settings")

        self.key_bind_settings_tab = QWidget()
        self.init_key_binding_tab()
        self.tabs.addTab(self.key_bind_settings_tab, "Key Bind")

        self.stream_tab = QWidget()
        self.init_stream_tab()
        self.tabs.addTab(self.stream_tab, "Stream")

    def init_stream_tab(self):
        # Layout for the YouTube streaming form
        form_layout = QFormLayout()

        # Input field for the YouTube livestream key
        self.youtube_key_input = QLineEdit()
        self.youtube_key_input.setPlaceholderText("Enter YouTube Livestream Key")
        form_layout.addRow("Livestream Key:", self.youtube_key_input)

        # Button to start the stream
        self.start_stream_button = QPushButton("Start Stream")
        self.start_stream_button.clicked.connect(lambda x: self.camera_manager.stop_stream() if self.camera_manager.is_stream else self.camera_manager.start_stream(self.youtube_key_input.text()))

        self.camera_manager.is_stream_stream.connect(lambda is_stream: self.on_stream(is_stream))

        # Add form and button to the layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.start_stream_button)
        layout.addStretch()  # Push content to the top

        self.stream_tab.setLayout(layout)

    def on_stream(self, is_stream):
        self.start_stream_button.setText("Stop Stream" if is_stream else "Start Stream")

    def init_key_binding_tab(self):
        key_bind_layout = QFormLayout()

        # For each key bind setting, add a button that allows editing
        settings_button = QKeySequenceEdit()
        replay_button = QKeySequenceEdit()
        record_button = QKeySequenceEdit()
        next_camera_button = QKeySequenceEdit()
        play_pause_button = QKeySequenceEdit()
        frame_forward_button = QKeySequenceEdit()
        frame_backward_button = QKeySequenceEdit()
        second_forward_button = QKeySequenceEdit()
        second_backward_button = QKeySequenceEdit()
        reset_zoom_button = QKeySequenceEdit()

        settings_button.setKeySequence(self.key_bind_manager.settings_key)
        replay_button.setKeySequence(self.key_bind_manager.replay_key)
        record_button.setKeySequence(self.key_bind_manager.record_key)
        next_camera_button.setKeySequence(self.key_bind_manager.next_camera_key)
        play_pause_button.setKeySequence(self.key_bind_manager.play_pause_key)
        frame_forward_button.setKeySequence(self.key_bind_manager.frame_forward_key)
        frame_backward_button.setKeySequence(self.key_bind_manager.frame_backward_key)
        second_forward_button.setKeySequence(self.key_bind_manager.second_forward_key)
        second_backward_button.setKeySequence(self.key_bind_manager.second_backward_key)
        reset_zoom_button.setKeySequence(self.key_bind_manager.reset_zoom_key)

        settings_button.editingFinished.connect(lambda: self.update_key_bind(settings_button, self.key_bind_manager.change_settings_key))
        replay_button.editingFinished.connect(lambda: self.update_key_bind(replay_button, self.key_bind_manager.change_replay_key))
        record_button.editingFinished.connect(lambda: self.update_key_bind(record_button, self.key_bind_manager.change_record_key))
        next_camera_button.editingFinished.connect(lambda: self.update_key_bind(next_camera_button, self.key_bind_manager.change_next_camera_key))
        play_pause_button.editingFinished.connect(lambda: self.update_key_bind(play_pause_button, self.key_bind_manager.change_play_pause_key))
        frame_forward_button.editingFinished.connect(lambda: self.update_key_bind(frame_forward_button, self.key_bind_manager.change_frame_forward_key))
        frame_backward_button.editingFinished.connect(lambda: self.update_key_bind(frame_backward_button, self.key_bind_manager.change_frame_backward_key))
        second_forward_button.editingFinished.connect(lambda: self.update_key_bind(second_forward_button, self.key_bind_manager.change_second_forward_key))
        second_backward_button.editingFinished.connect(lambda: self.update_key_bind(second_backward_button, self.key_bind_manager.change_second_backward_key))
        reset_zoom_button.editingFinished.connect(lambda: self.update_key_bind(reset_zoom_button, self.key_bind_manager.change_reset_zoom_key))

        key_bind_layout.addRow("Open Settings Shortcut:", settings_button)
        key_bind_layout.addRow("Open Replay Shortcut:", replay_button)
        key_bind_layout.addRow("Start Recording Shortcut:", record_button)
        key_bind_layout.addRow("Go to Next Camera Shortcut:", next_camera_button)
        key_bind_layout.addRow("Play/Pause Shortcut", play_pause_button)
        key_bind_layout.addRow("Frame Forward Shortcut:", frame_forward_button)
        key_bind_layout.addRow("Frame Backward Shortcut:", frame_backward_button)
        key_bind_layout.addRow("Second Forward Shortcut:", second_forward_button)
        key_bind_layout.addRow("Second Backward Shortcut:", second_backward_button)
        key_bind_layout.addRow("Reset Zoom Shortcut:", reset_zoom_button)

        self.key_bind_settings_tab.setLayout(key_bind_layout)

    def update_key_bind(self, button: QKeySequenceEdit, func):
        print(button.keySequence().toString())
        func(button.keySequence().toString())
        button.clearFocus()

    def init_camera_settings_tab(self):
        layout = QVBoxLayout()
        
        # Scroll Area for camera list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        self.toggle = QCheckBox()
        self.toggle.setChecked(self.camera_manager.is_scoreboard)
        self.toggle.clicked.connect(lambda x: self.set_scoreboard(x))

        # Add each camera to the scroll area
        for idx, cam in enumerate(self.camera_manager.get_all_cameras()):
            cam_frame = QFrame()
            cam_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            cam_layout = QVBoxLayout(cam_frame)

            cam_name = f"Camera {idx}"

            if idx == 0:
                cam_name = "Scoreboard"
            
            elif idx == 1:
                cam_name = "Primary Camera"

            # Header layout with camera name (bold) and remove button
            header_layout = QHBoxLayout()
            name_label = QLabel(cam_name)
            name_label.setFont(QFont("Arial", weight=QFont.Bold))
            header_layout.addWidget(name_label, alignment=Qt.AlignLeft)

            if idx == 0:
                header_layout.addWidget(self.toggle, alignment=Qt.AlignRight)
            
            elif idx == 1:
                pass

            else:
                remove_button = QPushButton()
                remove_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
                remove_button.setFlat(True)
                remove_button.clicked.connect(lambda _, cam_id=idx: self.remove_camera(cam_id))

                header_layout.addWidget(remove_button, alignment=Qt.AlignRight)
            cam_layout.addLayout(header_layout)

            # Horizontal layout for preview and update fields
            body_layout = QHBoxLayout()

            # Camera preview
            preview_label = VideoStreamWidget(f"{cam.get_source(idx)} ! video/x-raw,width={cam.resolution[0]},height={cam.resolution[1]},framerate={cam.fps}/1,format={cam.format} ! videoconvert ! videoscale ! video/x-raw,format=RGB,width=272,height=153 ! queue ! appsink name=sink emit-signals=True sync=True drop=False")
            self.video_widgets.append(preview_label)
            body_layout.addWidget(preview_label)

            # Update fields
            update_layout1 = QVBoxLayout()
            fps_input = QLineEdit(str(cam.fps))
            fps_input.setPlaceholderText("FPS")
            resolution_input = QLineEdit(f"{cam.resolution[0]}, {cam.resolution[1]}")
            resolution_input.setPlaceholderText("Resolution (width, height)")
            gstreamer_src_input = QLineEdit(cam.device)
            gstreamer_src_input.setPlaceholderText("GStreamer Source")

            update_layout1.addWidget(QLabel("FPS"))
            update_layout1.addWidget(fps_input)
            update_layout1.addWidget(QLabel("Resolution"))
            update_layout1.addWidget(resolution_input)
            update_layout1.addWidget(QLabel("GStreamer Source"))
            update_layout1.addWidget(gstreamer_src_input)
            update_layout1.addStretch(1)

            update_layout2 = QVBoxLayout()
            format_input = QLineEdit(str(cam.format))
            format_input.setPlaceholderText("Format")

            update_layout2.addWidget(QLabel("Format"))
            update_layout2.addWidget(format_input)
            update_layout2.addStretch(1)

            # Connect editingFinished to auto-update settings on change
            fps_input.editingFinished.connect(lambda cam_id=idx, fps_input=fps_input,
                res_input=resolution_input, src_input=gstreamer_src_input: 
                self.update_camera_settings(cam_id, fps_input, res_input, src_input, format_input))
            resolution_input.editingFinished.connect(lambda cam_id=idx, fps_input=fps_input,
                res_input=resolution_input, src_input=gstreamer_src_input: 
                self.update_camera_settings(cam_id, fps_input, res_input, src_input, format_input))
            gstreamer_src_input.editingFinished.connect(lambda cam_id=idx, fps_input=fps_input,
                res_input=resolution_input, src_input=gstreamer_src_input: 
                self.update_camera_settings(cam_id, fps_input, res_input, src_input, format_input))
            format_input.editingFinished.connect(lambda cam_id=idx, fps_input=fps_input,
                res_input=resolution_input, src_input=gstreamer_src_input, form_input=format_input: 
                self.update_camera_settings(cam_id, fps_input, res_input, src_input, form_input))

            body_layout.addLayout(update_layout1)
            body_layout.addLayout(update_layout2)

            cam_layout.addLayout(body_layout)
            scroll_layout.addWidget(cam_frame)

        # "Add Camera" button at the bottom
        add_cam_button = QPushButton("Add Camera")
        add_cam_button.clicked.connect(self.open_add_camera_dialog)
        scroll_layout.addWidget(add_cam_button, alignment=Qt.AlignCenter)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        self.camera_settings_tab.setLayout(layout)

    def open_add_camera_dialog(self):
        dialog = AddCameraDialog(self.camera_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_camera_list()

    def update_camera_settings(self, cam_id, fps_input, resolution_input, gstreamer_src_input, format_input):
        fps = int(fps_input.text()) if fps_input.text() else None
        resolution = tuple(map(int, resolution_input.text().split(','))) if resolution_input.text() else None
        gstreamer_src = gstreamer_src_input.text() if gstreamer_src_input.text() else None
        format = format_input.text() if format_input.text() else None
        print(format)
        self.camera_manager.update_camera(cam_id, fps, resolution, gstreamer_src, format)
        self.update_camera_list()

    def remove_camera(self, cam_id):
        self.camera_manager.remove_camera(cam_id)
        self.update_camera_list()

    def update_camera_list(self):
        self.clear_layout()
        self.stop()
        self.video_widgets.clear()
        self.init_tabs()
        self.start()

    def set_scoreboard(self, is_scoreboard):
        self.camera_manager.is_scoreboard = is_scoreboard
        self.camera_manager.save_cameras()
        print(is_scoreboard)

    def clear_layout(self):
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)

    def start(self):
        for widget in self.video_widgets:
            widget.start()
    
    def stop(self):
        for widget in self.video_widgets:
            widget.stop()
