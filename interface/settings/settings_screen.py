from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTabWidget, QFrame, QDialog, QCheckBox,
    QStyle, QSizePolicy, QKeySequenceEdit, QFormLayout, QGridLayout, QSpinBox
)
import gi
from PyQt5.QtGui import QPixmap, QIcon, QFont, QImage
from PyQt5.QtCore import Qt, QMetaObject, Q_ARG, pyqtSlot
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import cv2
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QApplication, QGroupBox
)
from cv2_enumerate_cameras import enumerate_cameras

import ipaddress

from interface.settings.widgets.my_line_edit import MyLineEdit
from interface.settings.widgets.video_stream_widget import VideoStreamWidget

from app.injector import Injector
from app.webserver_manager import WebServerManager
from app.key_bind_manager import KeyBindManager
from app.camera_manager import CameraManager
from app.udp_manager import UdpManager
from app.licence_manager import LicenceManager
from app.external_screen_manager import ExternalScreenManager
from app.obs_manager import OBSManager

class SettingsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.key_bind_manager: KeyBindManager = Injector.find(KeyBindManager)
        self.webserver_manager: WebServerManager = Injector.find(WebServerManager)
        self.camera_manager: CameraManager = Injector.find(CameraManager)
        self.udp_manager: UdpManager = Injector.find(UdpManager)
        self.licence_manager: LicenceManager = Injector.find(LicenceManager)
        self.external_screen_manager: ExternalScreenManager = Injector.find(ExternalScreenManager)
        self.obs_manager: OBSManager = Injector.find(OBSManager)
        self.video_widgets = []
        self.is_update = False
        self.init_ui()

        # self.licence_manager.licence_valid.connect(self.on_licence_valid)
        # self.licence_manager.licence_invalid.connect(self.on_licence_invalid)

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
        self.camera_settings_tab = QWidget()
        self.init_camera_settings_tab()
        self.tabs.addTab(self.camera_settings_tab, "Video Replay")

        self.external_screen_tab = QWidget()
        self.init_external_screen_tab()
        self.tabs.addTab(self.external_screen_tab, "External Screen")

        self.stream_tab = QWidget()
        self.init_stream_tab()
        self.tabs.addTab(self.stream_tab, "Stream")

        self.udp_settings_tab = QWidget()
        self.init_udp_settings_tab()
        self.tabs.addTab(self.udp_settings_tab, "Scoreboard Listener")

        self.key_bind_settings_tab = QWidget()
        self.init_key_binding_tab()
        self.tabs.addTab(self.key_bind_settings_tab, "Key Binds")

        self.licence_tab = QWidget()
        self.init_licence_tab()
        self.tabs.addTab(self.licence_tab, "Licence")

    def init_stream_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # ===== Section 1: OBS Integration =====
        obs_title = QLabel("OBS Studio Control")
        obs_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(obs_title)

        obs_frame = QFrame()
        obs_layout = QFormLayout(obs_frame)
        
        # 1. Configuration Inputs
        obs_pass_input = MyLineEdit()
        obs_pass_input.setEchoMode(QLineEdit.Password)
        obs_pass_input.setText(self.obs_manager.obs_password)
        obs_pass_input.textChanged.connect(lambda t: setattr(self.obs_manager, "obs_password", t))
        obs_layout.addRow("OBS Password:", obs_pass_input)

        layout.addWidget(obs_frame)

        # 2. Launch Buttons (Launch with specific Collections)
        btn_layout = QHBoxLayout()
        
        btn_launch_basic = QPushButton("Launch OBS (Basic Mode)")
        btn_launch_basic.clicked.connect(lambda: self.launch_and_setup_obs("basic"))
        
        btn_launch_pro = QPushButton("Launch OBS (Pro Mode)")
        btn_launch_pro.clicked.connect(lambda: self.launch_and_setup_obs("pro"))

        btn_layout.addWidget(btn_launch_basic)
        btn_layout.addWidget(btn_launch_pro)
        layout.addLayout(btn_layout)

        # 3. Live Controls (Only work if OBS is open)
        control_group = QGroupBox("Live Controls")
        control_layout = QHBoxLayout()

        btn_connect = QPushButton("Connect WebSocket")
        btn_connect.clicked.connect(self.obs_manager.connect_to_obs)
        
        btn_start_stream = QPushButton("Start Streaming")
        btn_start_stream.setStyleSheet("background-color: green; color: white;")
        btn_start_stream.clicked.connect(self.obs_manager.start_streaming)

        btn_stop_stream = QPushButton("Stop Streaming")
        btn_stop_stream.setStyleSheet("background-color: red; color: white;")
        btn_stop_stream.clicked.connect(self.obs_manager.stop_streaming)

        control_layout.addWidget(btn_connect)
        control_layout.addWidget(btn_start_stream)
        control_layout.addWidget(btn_stop_stream)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # 4. Scene Switcher Example
        scene_group = QGroupBox("Scene Switcher")
        scene_layout = QHBoxLayout()
        
        btn_scoreboard = QPushButton("Start Soon Scene")
        btn_scoreboard.clicked.connect(lambda: self.obs_manager.set_scene("Start Soon Scene"))
        scene_layout.addWidget(btn_scoreboard)

        btn_scoreboard = QPushButton("Main Scene")
        btn_scoreboard.clicked.connect(lambda: self.obs_manager.set_scene("Main Scene"))
        scene_layout.addWidget(btn_scoreboard)

        btn_scoreboard = QPushButton("IVR Scene")
        btn_scoreboard.clicked.connect(lambda: self.obs_manager.set_scene("IVR Scene"))
        scene_layout.addWidget(btn_scoreboard)

        btn_scoreboard = QPushButton("IVR Closeup Scene")
        btn_scoreboard.clicked.connect(lambda: self.obs_manager.set_scene("IVR Closeup Scene"))
        scene_layout.addWidget(btn_scoreboard)

        scene_group.setLayout(scene_layout)
        layout.addWidget(scene_group)

        layout.addStretch(1)
        self.stream_tab.setLayout(layout)

    def launch_and_setup_obs(self, mode):
        """
        1. Launches OBS with the correct collection CLI argument.
        2. Waits a moment (optional, or rely on manual Connect).
        3. Connects WebSocket.
        """
        self.obs_manager.launch_obs(mode=mode)
        
        # Optional: Try to auto-connect after 5 seconds
        # QTimer.singleShot(5000, self.obs_manager.connect_to_obs)

    def init_external_screen_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel("External Screen Manager")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)

        # Setting: Main Display
        self.main_display_input = QLineEdit()
        self.main_display_input.setText(self.external_screen_manager.main_display)
        self.main_display_input.setPlaceholderText("e.g., eDP-1")
        self.main_display_input.editingFinished.connect(
            lambda: setattr(self.external_screen_manager, 'main_display', self.main_display_input.text())
        )
        form_layout.addRow(QLabel("Main Display Name:"), self.main_display_input)
        
        # Setting: External Display
        self.ext_display_input = QLineEdit()
        self.ext_display_input.setText(self.external_screen_manager.external_display)
        self.ext_display_input.setPlaceholderText("e.g., HDMI-1")
        self.ext_display_input.editingFinished.connect(
            lambda: setattr(self.external_screen_manager, 'external_display', self.ext_display_input.text())
        )
        form_layout.addRow(QLabel("External Display Name:"), self.ext_display_input)

        # Setting: Workspace
        self.workspace_spin = QSpinBox()
        self.workspace_spin.setMinimum(1)
        self.workspace_spin.setMaximum(12) # Reasonable max
        self.workspace_spin.setValue(self.external_screen_manager.target_workspace)
        self.workspace_spin.valueChanged.connect(
            lambda val: setattr(self.external_screen_manager, 'target_workspace', val)
        )
        form_layout.addRow(QLabel("Target Workspace:"), self.workspace_spin)
        
        # Setting: Window Title
        self.window_title_input = QLineEdit()
        self.window_title_input.setText(self.external_screen_manager.window_title)
        self.window_title_input.editingFinished.connect(
            lambda: setattr(self.external_screen_manager, 'window_title', self.window_title_input.text())
        )
        form_layout.addRow(QLabel("Window Title:"), self.window_title_input)

        layout.addWidget(form_frame)

        # --- Action Buttons ---
        self.start_ext_screen_button = QPushButton("Start External Screen")
        self.start_ext_screen_button.clicked.connect(self.toggle_external_screen)
        layout.addWidget(self.start_ext_screen_button)
        
        self.toggle_display_mode_button = QPushButton("Toggle Mirror/Extended Mode")
        self.toggle_display_mode_button.clicked.connect(self.external_screen_manager.toggle_display_mode)
        layout.addWidget(self.toggle_display_mode_button)

        # Connect to the manager's state signal
        self.external_screen_manager.screen_state_changed.connect(self.on_external_screen_state_change)
        # Set initial button state
        self.on_external_screen_state_change(self.external_screen_manager.is_running)

        layout.addStretch(1)
        self.external_screen_tab.setLayout(layout)

    # --- Slots for External Screen Tab ---
    def toggle_external_screen(self):
        if self.external_screen_manager.is_running:
            self.external_screen_manager.stop_external_screen()
        else:
            self.external_screen_manager.start_external_screen()

    @pyqtSlot(bool)
    def on_external_screen_state_change(self, is_running):
        self.start_ext_screen_button.setText("Stop External Screen" if is_running else "Start External Screen")

    def update_external_camera_idx(self, index):
        # index is 0-based, camera_idx is 1-based
        self.external_screen_manager.external_camera_idx = index + 1


    def init_udp_settings_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel("Tk-Strike UDP Listener")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)

        self.udp_default = QCheckBox()
        self.udp_default.setChecked(self.udp_manager.udp_default)
        self.udp_default.clicked.connect(lambda x: self.set_udp_as_default(x))
        form_layout.addRow(QLabel("Set as Default:"), self.udp_default)
        
        self.udp_port_input = QLineEdit()
        self.udp_port_input.setPlaceholderText("9998")
        self.udp_port_input.setText(str(self.udp_manager.udp_port))
        self.udp_port_input.editingFinished.connect(self.update_udp_port)
        form_layout.addRow(QLabel("UDP Listener Port:"), self.udp_port_input)
        
        layout.addWidget(form_frame)

        self.start_udp_button = QPushButton("Start UDP Listener")
        self.start_udp_button.clicked.connect(self.toggle_udp_listener)
        layout.addWidget(self.start_udp_button)
        
        # Connect to the manager's state signal to update the button text
        self.udp_manager.listener_state_changed.connect(self.on_udp_listener_state_change)
        # Set initial button state
        self.on_udp_listener_state_change(self.udp_manager.thread.isRunning())

        layout.addStretch(1)
        self.udp_settings_tab.setLayout(layout)

    def set_udp_as_default(self, is_default):
        self.udp_manager.udp_default = is_default

    # NEW methods and slots for handling the UDP tab
    def toggle_udp_listener(self):
        if self.udp_manager.thread.isRunning():
            self.udp_manager.stop_listener()
        else:
            self.udp_manager.start_listener()

    @pyqtSlot(bool)
    def on_udp_listener_state_change(self, is_running):
        self.start_udp_button.setText("Stop UDP Listener" if is_running else "Start UDP Listener")

    def update_udp_port(self):
        self.udp_manager.set_port(self.udp_port_input.text())
        self.udp_port_input.clearFocus()

    @pyqtSlot(bool)
    def on_webserver_state_change(self, is_running):
        self.start_webserver_button.setText("Stop Pro YouTube Livetream Server" if is_running else "Start Pro YouTube Livetream Server")

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
            lambda fn_captured=field_name, widget=seq_edit: self.update_key_bind(
                    fn_captured, 
                    widget.keySequence().toString(), 
                    widget
                )
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
        form_layout.addRow(QLabel("Relese Records:"), delete_toggle)

        layout.addWidget(start_frame)

        # Grid layout for camera previews
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        columns = 5  # Number of columns in the grid

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
            if idx == 0:
                # Scoreboard (SHM Source)
                source_pipe = self.camera_manager.get_shmsink(0)
                width = 1280
                height = 720
            else:
                # RTSP Cameras (Direct Source, needs full pipeline)
                source_pipe = f"{"videotestsrc" if self.camera_manager.debug else self.camera_manager.get_camera(idx)} ! vaapipostproc"
                width = self.camera_manager.res_width
                height = self.camera_manager.res_height
                
            # Construct the final pipeline string for the preview
            pipeline_desc = (
                f"{source_pipe} ! video/x-raw,width={width},height={height},framerate={self.camera_manager.fps}/1,format=NV12 ! "
                f"videoconvert ! videoscale ! video/x-raw,format=RGB,width=272,height=153 ! "
                f"queue ! appsink name=sink emit-signals=True sync=True drop=False"
            )

            preview_label = VideoStreamWidget(pipeline_desc, 272, 153)
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

    def set_debug(self, debug):
        self.camera_manager.debug = debug
        # self.camera_manager.save_cameras()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()

    def set_release_records(self, delete_records):
        self.camera_manager.delete_records = delete_records
        # self.camera_manager.save_cameras()

    def set_live(self, key):
        self.camera_manager.live_key = key
        # self.camera_manager.save_cameras()

    def set_scoreboard(self, is_scoreboard):
        self.camera_manager.is_scoreboard = is_scoreboard
        # self.camera_manager.save_cameras()
        print(is_scoreboard)

    def set_resolution(self, resolution: int):
        self.camera_manager.res_height = resolution
        self.camera_manager.res_width = resolution // 9 * 16
        # self.camera_manager.save_cameras()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()
        print(f"{resolution // 9 * 16}:{resolution}")

    def set_court(self, court: int):
        self.camera_manager.court = court
        # self.camera_manager.save_cameras()
        self.camera_manager.reload_shmsink()
        self.update_camera_list()

    def set_camera_idx(self, idx: int):
        self.camera_manager.camera_idx = idx
        # self.camera_manager.save_cameras()
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

    def init_licence_tab(self):
        """Creates the UI for the Licence & API Settings tab."""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel("Licence & API Settings")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(10)
        form_layout.setHorizontalSpacing(20)

        # --- Licence Key Input ---
        self.licence_key_input = MyLineEdit()
        self.licence_key_input.setPlaceholderText("Enter your licence key")
        self.licence_key_input.setText(self.licence_manager.licence_key)
        self.licence_key_input.editingFinished.connect(self.update_licence_key)
        form_layout.addRow(QLabel("Licence Key:"), self.licence_key_input)

        # --- Licence Status Label ---
        self.licence_status_label = QLabel("Status: Unknown")
        self.licence_status_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow(QLabel(""), self.licence_status_label)
        
        layout.addWidget(form_frame)

        # --- Verify Button ---
        self.verify_licence_button = QPushButton("Verify Licence Key")
        self.verify_licence_button.clicked.connect(self.on_verify_licence_clicked)
        # Set a max width so it doesn't look too wide
        self.verify_licence_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed) 
        layout.addWidget(self.verify_licence_button, alignment=Qt.AlignLeft)
        
        layout.addStretch(1)
        self.licence_tab.setLayout(layout)

        # Trigger an initial validation check when the app loads
        # Use a small delay to ensure everything is initialized
        # QMetaObject.invokeMethod(self, "on_verify_licence_clicked", Qt.QueuedConnection)

    def update_licence_key(self):
        """Called when the licence key text field loses focus."""
        key = self.licence_key_input.text()
        self.licence_manager.set_licence_key(key)
        self.licence_key_input.clearFocus()
        self.licence_status_label.setText("Status: Changed. Click Verify.")
        self.licence_status_label.setStyleSheet("font-weight: bold; color: #FFA500;") # Orange

    def on_verify_licence_clicked(self):
        """Triggers the API validation call in the LicenceManager."""
        # Ensure a key is actually entered before trying
        if not self.licence_manager.licence_key:
            self.licence_status_label.setText("Status: Please enter a key.")
            self.licence_status_label.setStyleSheet("font-weight: bold; color: red;")
            return

        self.licence_status_label.setText("Status: Verifying...")
        self.licence_status_label.setStyleSheet("font-weight: bold; color: #FFA500;") # Orange
        
        # This assumes you will add the 'validate_licence' method (Step 2 below)
        # to your LicenceManager
        self.licence_manager.validate_licence() 

    @pyqtSlot(dict)
    def on_licence_valid(self, validation_data):
        """Slot for the 'licence_valid' signal from LicenceManager."""
        # API call was a success!
        message = validation_data.get('message', 'Valid')
        self.licence_status_label.setText(f"Status: {message}")
        self.licence_status_label.setStyleSheet("font-weight: bold; color: green;")
        
    @pyqtSlot(str)
    def on_licence_invalid(self, error_message):
        """Slot for the 'licence_invalid' (or 'api_error') signal."""
        # API call failed (auth error, connection error, etc.)
        self.licence_status_label.setText(f"Status: Invalid ({error_message})")
        self.licence_status_label.setStyleSheet("font-weight: bold; color: red;")

    def clear_layout(self):
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)

    def start(self):
        for widget in self.video_widgets:
            widget.start()
    
    def stop(self):
        for widget in self.video_widgets:
            widget.stop()
