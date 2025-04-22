from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTabWidget, QFrame, QDialog, QCheckBox,
    QStyle, QSizePolicy, QKeySequenceEdit, QFormLayout, QGridLayout
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
    def __init__(self, controller_manager, key_bind_manager, camera_manager):
        super().__init__()
        self.controller_manager = controller_manager
        self.key_bind_manager = key_bind_manager
        self.camera_manager = camera_manager
        self.video_widgets = []
        self.is_update = False
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

        if (int(self.cam_combo.currentText()[-1]) != self.camera_manager.camera_idx):
            self.set_camera_idx(int(self.cam_combo.currentText()[-1]))

    def init_tabs(self):
        print("ropop")
        self.camera_settings_tab = QWidget()
        self.init_camera_settings_tab()
        self.tabs.addTab(self.camera_settings_tab, "Camera Settings")

        self.stream_tab = QWidget()
        self.init_stream_tab()
        self.tabs.addTab(self.stream_tab, "Stream")

        self.key_bind_settings_tab = QWidget()
        self.init_key_binding_tab()
        self.tabs.addTab(self.key_bind_settings_tab, "Key Bind")

        self.controller_tab = QWidget()
        self.init_controller_tab()
        self.tabs.addTab(self.controller_tab, "Controller")

    def init_controller_tab(self):
        # Layout for the YouTube streaming form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setHorizontalSpacing(50)

        # Input field for the YouTube livestream key
        controller_input = QLineEdit()
        controller_input.setText(self.controller_manager.command_str)
        controller_input.setPlaceholderText("Enter controller starter command")
        form_layout.addRow("Controller command:", controller_input)

        # Button to start the stream
        submit_button = QPushButton("Save controller starter command")
        submit_button.clicked.connect(lambda _: self.save_controller(controller_input.text()))

        # Add form and button to the layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(submit_button)
        layout.addStretch()  # Push content to the top

        self.controller_tab.setLayout(layout)

    def save_controller(self, command):
        self.controller_manager.save_command(command)
        self.controller_manager.reload()
        self.clearFocus()

    def init_stream_tab(self):
        layout = QVBoxLayout()

        start_frame = QFrame()
        start_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        # Main horizontal layout
        main_layout = QHBoxLayout(start_frame)

        # Left layout for the preview (compact)
        left_layout = QVBoxLayout()

        # Camera preview area (left side)
        preview_label = VideoStreamWidget(f"{self.camera_manager.get_shmsink(self.camera_manager.live_camera_idx)} ! video/x-raw,width={self.camera_manager.res_width},height={self.camera_manager.res_height},framerate={self.camera_manager.fps}/1,format=NV12 ! videoconvert ! videoscale ! video/x-raw,format=RGB,width=272,height=153 ! queue ! appsink name=sink emit-signals=True sync=True drop=False")
        self.video_widgets.append(preview_label)
        left_layout.addWidget(preview_label)

        # Right layout for camera controls (compact)
        right_layout = QVBoxLayout()
        form_frame = QFrame()
        form_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        form_layout = QFormLayout(form_frame)  # Form layout for label-field alignment
        form_layout.setSpacing(10)
        form_layout.setHorizontalSpacing(50)
        form_layout.setLabelAlignment(Qt.AlignLeft)  # Ensure labels align to the left

        # Camera ID combo box and label
        camera_id_label = QLabel("Camera ID:")
        camera_id_combo = QComboBox()
        camera_id_combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        camera_id_combo.addItems([f"Camera {i+1}" for i in range(self.camera_manager.camera_count)])  # Populate with actual cameras
        form_layout.addRow(camera_id_label, camera_id_combo)

        # Livestream key input
        youtube_key_input = QLineEdit()
        youtube_key_input.setPlaceholderText("Enter YouTube Livestream Key")
        youtube_key_input.setText(self.camera_manager.live_key)
        form_layout.addRow(QLabel("Livestream Key:"), youtube_key_input)

        # Start/Stop livestream button
        self.start_stream_button = QPushButton("Start Stream")
        self.start_stream_button.clicked.connect(lambda x: self.toggle_stream(1, youtube_key_input.text()))

        # Add form layout and button to the right layout
        right_layout.addWidget(form_frame)
        right_layout.addWidget(self.start_stream_button)

        # Set the layout sizes to prevent stretching
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        # Connecting the stream status
        self.camera_manager.is_stream_stream.connect(lambda is_stream: self.on_stream(is_stream))

        layout.addWidget(start_frame)
        space = QLabel("")
        space.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(space, alignment=Qt.AlignCenter)

        self.stream_tab.setLayout(layout)

    def on_stream(self, is_stream):
        self.start_stream_button.setText("Stop Stream" if is_stream else "Start Stream")

    

    def toggle_stream(self, idx, key):
        if self.camera_manager.is_stream:
            self.camera_manager.stop_stream() 

        else:
            self.set_live(key)
            self.camera_manager.start_stream()

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
        if button.keySequence().toString() != "":
            func(button.keySequence().toString())
        button.clearFocus()

    def init_camera_settings_tab(self):
        layout = QVBoxLayout()

        self.toggle = QCheckBox()
        self.toggle.setChecked(self.camera_manager.is_scoreboard)
        self.toggle.clicked.connect(lambda x: self.set_scoreboard(x))

        start_frame = QFrame()
        start_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        form_layout = QFormLayout(start_frame)  # Form layout for label-field alignment
        form_layout.setSpacing(10)
        form_layout.setHorizontalSpacing(50)
        form_layout.setLabelAlignment(Qt.AlignLeft)  # Ensure labels align to the left

        vaapi_toggle = QCheckBox()
        vaapi_toggle.setChecked(self.camera_manager.vaapi)
        vaapi_toggle.clicked.connect(lambda x: self.set_vaapi(x))

        delete_toggle = QCheckBox()
        delete_toggle.setChecked(self.camera_manager.delete_records)
        delete_toggle.clicked.connect(lambda x: self.set_release_records(x))

        debug_toggle = QCheckBox()
        debug_toggle.setChecked(self.camera_manager.debug)
        debug_toggle.clicked.connect(lambda x: self.set_debug(x))

        res_combo = QComboBox()
        res_combo.addItems(["480", "720", "1080"])
        res_combo.setCurrentText(str(self.camera_manager.res_height))
        res_combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        res_combo.currentTextChanged.connect(lambda num: self.set_resolution(int(num)))

        self.cam_combo = QComboBox()
        self.cam_combo.addItems([f"/dev/video{i}" for i in self.get_connected_cameras()])
        self.cam_combo.setCurrentText(f"/dev/video{self.camera_manager.camera_idx}")
        self.cam_combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.cam_combo.currentTextChanged.connect(lambda device: self.set_camera_idx(int(device[-1])))

        court_combo = QComboBox()
        court_combo.addItems([f"{i}" for i in range(1, 26)])
        court_combo.setCurrentText(str(self.camera_manager.court))
        court_combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        court_combo.currentTextChanged.connect(lambda num: self.set_court(int(num)))

        form_layout.addRow(QLabel("Select Camera:"), self.cam_combo)
        form_layout.addRow(QLabel("Select Court:"), court_combo)
        form_layout.addRow(QLabel("Debug Mode:"), debug_toggle)
        form_layout.addRow(QLabel("Resolution:"), res_combo)
        form_layout.addRow(QLabel("VA-API Support:"), vaapi_toggle)
        form_layout.addRow(QLabel("Relese Records:"), delete_toggle)

        layout.addWidget(start_frame)

        # Grid layout for camera previews
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        columns = 3  # Number of columns in the grid

        # Add each camera to the grid
        for idx in range(self.camera_manager.camera_count+1):
            row = idx // columns
            col = idx % columns

            cam_frame = QFrame()
            cam_frame.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            cam_layout = QVBoxLayout(cam_frame)

            cam_name = f"Camera {idx}"

            if idx == 0:
                cam_name = "Scoreboard"
            
            elif idx == 1:
                cam_name = "Primary Camera"

            # Header layout with camera name (bold) and remove button
            header_layout = QHBoxLayout()
            name_label = QLabel(cam_name)
            header_layout.addWidget(name_label, alignment=Qt.AlignLeft)

            if idx == 0:
                header_layout.addWidget(self.toggle, alignment=Qt.AlignRight)
            
            elif idx == self.camera_manager.camera_count:
                remove_button = QPushButton()
                remove_button.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
                remove_button.setFixedHeight(13)
                remove_button.setFlat(True)
                remove_button.clicked.connect(lambda _, cam_id=idx: self.remove_camera(cam_id))

                header_layout.addWidget(remove_button, alignment=Qt.AlignRight)

            cam_layout.addLayout(header_layout)

            # Camera preview
            preview_label = VideoStreamWidget(f"{self.camera_manager.get_shmsink(idx)} ! video/x-raw,width={"640" if idx == 0 else self.camera_manager.res_width},height={"480" if idx == 0 else self.camera_manager.res_height},framerate={self.camera_manager.fps}/1,format=NV12 ! videoconvert ! videoscale ! video/x-raw,format=RGB,width=272,height=153 ! queue ! appsink name=sink emit-signals=True sync=True drop=False")
            self.video_widgets.append(preview_label)

            cam_layout.addWidget(preview_label)
            cam_frame.setLayout(cam_layout)

            # Add to grid
            grid_layout.addWidget(cam_frame, row, col)

        add_button = QPushButton("Add Camera")
        add_button.setFixedHeight(200)
        add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        add_button.clicked.connect(self.open_add_camera_dialog)
        grid_layout.addWidget(add_button, (self.camera_manager.camera_count+1) // columns, (self.camera_manager.camera_count+1) % columns)

        layout.addLayout(grid_layout)

        # "Add Camera" button at the bottom
        space = QLabel("")
        layout.addWidget(space, alignment=Qt.AlignCenter)

        self.camera_settings_tab.setLayout(layout)

    def open_add_camera_dialog(self):
        #dialog = AddCameraDialog(self.camera_manager, self)
        #if dialog.exec_() == QDialog.Accepted:
        #    self.update_camera_list()
        self.camera_manager.add_camera()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()

    def get_connected_cameras(self):
        all_camera_idx = []
        for camera_info in enumerate_cameras(cv2.CAP_GSTREAMER):
            if camera_info.index != self.camera_manager.camera_idx:
                camera = cv2.VideoCapture(camera_info.index)
                if camera.isOpened():
                    all_camera_idx.append(camera_info.index)
                camera.release()
            
            else:
                all_camera_idx.insert(0, camera_info.index)

        return all_camera_idx

    def remove_camera(self, cam_id):
        #self.camera_manager.remove_camera(cam_id)
        self.camera_manager.remove_camera()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()

    def update_camera_list(self):
        self.clear_layout()
        self.stop()
        self.video_widgets.clear()
        self.init_tabs()
        self.start()

    def set_vaapi(self, vaapi):
        self.camera_manager.vaapi = vaapi
        self.camera_manager.save_cameras()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()

    def set_debug(self, debug):
        self.camera_manager.debug = debug
        self.camera_manager.save_cameras()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()

    def set_release_records(self, delete_records):
        self.camera_manager.delete_records = delete_records
        self.camera_manager.save_cameras()

    def set_live(self, key):
        self.camera_manager.live_key = key
        self.camera_manager.save_cameras()

    def set_scoreboard(self, is_scoreboard):
        self.camera_manager.is_scoreboard = is_scoreboard
        self.camera_manager.save_cameras()
        print(is_scoreboard)

    def set_resolution(self, resolution: int):
        self.camera_manager.res_height = resolution
        self.camera_manager.res_width = resolution // 9 * 16
        self.camera_manager.save_cameras()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()
        print(f"{resolution // 9 * 16}:{resolution}")

    def set_court(self, court: int):
        self.camera_manager.court = court
        self.camera_manager.save_cameras()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()

    def set_camera_idx(self, idx: int):
        self.camera_manager.camera_idx = idx
        self.camera_manager.save_cameras()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()

    def clear_layout(self):
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)

    def start(self):
        for widget in self.video_widgets:
            widget.start()
    
    def stop(self):
        for widget in self.video_widgets:
            widget.stop()
