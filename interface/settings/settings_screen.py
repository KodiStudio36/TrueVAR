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

import ipaddress

from interface.settings.widgets.my_line_edit import MyLineEdit
from interface.settings.widgets.video_stream_widget import VideoStreamWidget

from app.injector import Injector
from app.webserver_manager import WebServerManager
from app.key_bind_manager import KeyBindManager
from app.camera_manager import CameraManager

class SettingsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.key_bind_manager: KeyBindManager = Injector.find(KeyBindManager)
        self.webserver_manager: WebServerManager = Injector.find(WebServerManager)
        self.camera_manager: CameraManager = Injector.find(CameraManager)
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

        if (len(self.cam_combo.currentText()) > 0 and int(self.cam_combo.currentText()[-1]) != self.camera_manager.camera_idx):
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

    def init_stream_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)  # Set some spacing between sections for a cleaner look

        # ===== Section 1: Basic YouTube Livestream =====
        basic_title = QLabel("Basic YouTube Livestream")
        basic_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        # layout.addWidget(basic_title, alignment=Qt.AlignTop) # Removed, not needed with addStretch
        layout.addWidget(basic_title)

        start_frame = QFrame()
        # Adjust size policy to be more flexible
        start_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # Main horizontal layout
        main_layout = QHBoxLayout(start_frame)
        main_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop) # Align contents to the top-left
        main_layout.setSpacing(10)

        # Left layout for the preview (compact)
        left_layout = QVBoxLayout()
        preview_label = VideoStreamWidget(
            f"{self.camera_manager.get_shmsink(self.camera_manager.live_camera_idx)} "
            f"! video/x-raw,width={self.camera_manager.res_width},height={self.camera_manager.res_height},"
            f"framerate={self.camera_manager.fps}/1,format=NV12 ! videoconvert ! videoscale "
            f"! video/x-raw,format=RGB,width=272,height=153 ! queue ! appsink name=sink emit-signals=True sync=True drop=False",
        272, 153)
        self.video_widgets.append(preview_label)
        left_layout.addWidget(preview_label)

        # Right layout for camera controls (compact)
        right_layout = QVBoxLayout()
        form_frame = QFrame()
        form_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(10)
        form_layout.setHorizontalSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        # Camera ID combo box
        camera_id_combo = QComboBox()
        camera_id_combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        camera_id_combo.addItems([f"Camera {i+1}" for i in range(self.camera_manager.camera_count)])
        form_layout.addRow(QLabel("Camera ID:"), camera_id_combo)

        # Livestream key input
        youtube_key_input = MyLineEdit()
        youtube_key_input.setPlaceholderText("xxxx-xxxx-xxxx-xxxx-xxxx")
        youtube_key_input.setText(self.camera_manager.live_key)
        form_layout.addRow(QLabel("Livestream Key:"), youtube_key_input)

        # Start/Stop livestream button
        self.start_stream_button = QPushButton("Start Basic YouTube Livetream")
        self.start_stream_button.clicked.connect(lambda x: self.toggle_stream(1, youtube_key_input.text()))

        right_layout.addWidget(form_frame)
        right_layout.addWidget(self.start_stream_button)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.camera_manager.is_stream_stream.connect(lambda is_stream: self.on_stream(is_stream))

        layout.addWidget(start_frame)

        # Divider line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # ===== Section 2: Pro YouTube Livestream =====
        pro_title = QLabel("Pro YouTube Livestream")
        pro_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(pro_title)

        pro_form_frame = QFrame()
        # Adjust size policy for a tighter fit
        pro_form_layout = QFormLayout(pro_form_frame)
        pro_form_layout.setSpacing(10)
        pro_form_layout.setHorizontalSpacing(20)

        udp_port_input = MyLineEdit()
        udp_port_input.setPlaceholderText("9998")
        udp_port_input.setText(str(self.webserver_manager.udp_port))
        udp_port_input.textChanged.connect(lambda text: setattr(self.webserver_manager, "udp_port", int(text)))
        pro_form_layout.addRow(QLabel(f"Tk-Strike UDP Port:"), udp_port_input)

        web_port_input = MyLineEdit()
        web_port_input.setPlaceholderText("8000")
        web_port_input.setText(str(self.webserver_manager.webserver_port))
        web_port_input.textChanged.connect(lambda text: setattr(self.webserver_manager, "webserver_port", int(text)))
        pro_form_layout.addRow(QLabel(f"WebServer Port:"), web_port_input)

        obs_port_input = MyLineEdit()
        obs_port_input.setPlaceholderText("4455")
        obs_port_input.setText(str(self.webserver_manager.obs_port))
        obs_port_input.textChanged.connect(lambda text: setattr(self.webserver_manager, "obs_port", int(text)))
        pro_form_layout.addRow(QLabel(f"OBS WebSocket Port:"), obs_port_input)

        obs_pass_input = MyLineEdit()
        obs_pass_input.setPlaceholderText("Enter OBS WebSocket Password")
        obs_pass_input.setText(self.webserver_manager.obs_pass)
        obs_pass_input.textChanged.connect(lambda text: setattr(self.webserver_manager, "obs_pass", text))
        pro_form_layout.addRow(QLabel(f"OBS WebSocket Pass:"), obs_pass_input)

        layout.addWidget(pro_form_frame)

        # Start widgets server button
        start_widgets_server_btn = QPushButton(f"{"Stop" if self.webserver_manager.thread.isRunning() else "Start"} Pro YouTube Livetream Server")
        start_widgets_server_btn.clicked.connect(lambda x: self.toggle_webserver())
        layout.addWidget(start_widgets_server_btn)

        # Add a stretch to push all content to the top
        layout.addStretch(1)

        self.stream_tab.setLayout(layout)


    def on_stream(self, is_stream):
        self.start_stream_button.setText("Stop Stream" if is_stream else "Start Stream")    

    def toggle_stream(self, idx, key):
        if self.camera_manager.is_stream:
            self.camera_manager.stop_stream() 

        else:
            self.set_live(key)
            self.camera_manager.start_stream()

    def toggle_webserver(self):
        if self.webserver_manager.thread.isRunning():
            self.webserver_manager.stop_servers()

        else:
            self.webserver_manager.start_servers()


    def init_key_binding_tab(self):
        self.key_bind_layout = QFormLayout()

        self.key_bind_widgets = {}

        for field_name in self.key_bind_manager._settings_fields:
            seq_edit = QKeySequenceEdit()
            seq_edit.setKeySequence(getattr(self.key_bind_manager, field_name))
            seq_edit.editingFinished.connect(
                lambda fn=field_name, widget=seq_edit: self.update_key_bind(fn, widget.keySequence().toString(), widget)
            )
            self.key_bind_widgets[field_name] = seq_edit
            self.key_bind_layout.addRow(field_name.replace("_", " ").title() + ":", seq_edit)

        self.key_bind_settings_tab.setLayout(self.key_bind_layout)

    def update_key_bind(self, fn, key, widget):
        if key != "":
            setattr(self.key_bind_manager, fn, key)
        widget.clearFocus()

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

        self.network_ip_input = MyLineEdit()
        self.network_ip_input.setPlaceholderText("x.x.x.x")
        self.network_ip_input.setText(f"{self.camera_manager.network_ip}0")
        self.network_ip_input.editingFinished.connect(lambda: self.set_network_ip(self.network_ip_input.text()))

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

        cam_layout_h = QHBoxLayout()
        cam_layout_h.setSpacing(10)

        self.cam_combo = QComboBox()
        self.cam_combo.addItems([f"/dev/video{i}" for i in self.get_connected_cameras()])
        self.cam_combo.setCurrentText(f"/dev/video{self.camera_manager.camera_idx}")
        self.cam_combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.cam_combo.currentTextChanged.connect(lambda device: self.set_camera_idx(int(device[-1])))

        refresh_button = QPushButton()
        refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        refresh_button.setFixedHeight(self.cam_combo.sizeHint().height())  # match height
        refresh_button.setFixedWidth(self.cam_combo.sizeHint().height())  # match height
        refresh_button.clicked.connect(self.refresh_camera_list)

        cam_layout_h.addWidget(self.cam_combo)
        cam_layout_h.addWidget(refresh_button)

        court_combo = QComboBox()
        court_combo.addItems([f"{i}" for i in range(1, 26)])
        court_combo.setCurrentText(str(self.camera_manager.court))
        court_combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        court_combo.currentTextChanged.connect(lambda num: self.set_court(int(num)))

        form_layout.addRow(QLabel("Network ip address:"), self.network_ip_input)
        form_layout.addRow(QLabel("Select Camera:"), cam_layout_h)
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
            preview_label = VideoStreamWidget(f"{self.camera_manager.get_shmsink(idx)} ! video/x-raw,width={"640" if idx == 0 else self.camera_manager.res_width},height={"480" if idx == 0 else self.camera_manager.res_height},framerate={self.camera_manager.fps}/1,format=NV12 ! videoconvert ! videoscale ! video/x-raw,format=RGB,width=272,height=153 ! queue ! appsink name=sink emit-signals=True sync=True drop=False", 272, 153)
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

    def refresh_camera_list(self):
        self.camera_manager.reload_shmsink()
        self.update_camera_list()

    def set_network_ip(self, ip: str):
        try:
            if not isinstance(ipaddress.ip_address(ip), ipaddress.IPv4Address):
                raise ValueError()
            
            self.network_ip_input.setStyleSheet("")
            print(ip[:-len(ip.split(".")[-1])])
            self.camera_manager.network_ip = ip[:-len(ip.split(".")[-1])]
        except ValueError:
            self.network_ip_input.setStyleSheet("border: 2px solid red;")

        self.network_ip_input.clearFocus()

    def clear_layout(self):
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)

    def start(self):
        for widget in self.video_widgets:
            widget.start()
    
    def stop(self):
        for widget in self.video_widgets:
            widget.stop()
